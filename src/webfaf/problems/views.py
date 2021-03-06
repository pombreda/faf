import datetime
import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from sqlalchemy import func, sql

import pyfaf
from pyfaf.queries import (get_report_by_hash,
                           query_hot_problems,
                           query_longterm_problems)
from pyfaf.storage.problem import Problem
from pyfaf.storage.opsys import OpSysRelease, Arch, Package
from pyfaf.storage.report import (Report,
                                  ReportArch,
                                  ReportBtHash,
                                  ReportOpSysRelease,
                                  ReportExecutable,
                                  ReportPackage,
                                  ReportUnknownPackage)
from webfaf.common.forms import OsAssociateComponentFilterForm
from webfaf.common.utils import paginate, flatten
from webfaf.common.utils import WebfafJSONEncoder
from operator import itemgetter


def get_week_date_before(nweeks):
    curdate = datetime.date.today()
    return curdate - datetime.timedelta(weeks=nweeks,days=curdate.weekday())

def get_month_date_before(nmonths):
    curdate = datetime.date.today()
    subtract = datetime.timedelta(days=1)
    while nmonths != 0:
        curdate.replace(day=1)
        curdate -= subtract
        nmonths -= 1

    curdate.replace(day=1)
    return curdate

def hot(request, *args, **kwargs):
    db = pyfaf.storage.getDatabase()
    params = dict(request.REQUEST)
    params.update(kwargs)
    form = OsAssociateComponentFilterForm(db, params)
    last_date = datetime.date.today() - datetime.timedelta(days=14)

    ids = (r[0] for r in form.get_release_selection())

    problems = query_hot_problems(db,
        flatten(ids),
        form.get_component_selection(),
        last_date)

    if "application/json" in request.META.get("HTTP_ACCEPT"):
        return HttpResponse(json.dumps(problems, cls=WebfafJSONEncoder),
                            status=200, mimetype="application/json")
    else:
        problems = paginate(problems, request)
        forward = {'problems': problems,
                   'form': form}

        return render_to_response('problems/hot.html',
                                  forward,
                                  context_instance=RequestContext(request))

def longterm(request, *args, **kwargs):
    db = pyfaf.storage.getDatabase()
    params = dict(request.REQUEST)
    params.update(kwargs)
    form = OsAssociateComponentFilterForm(db, params)

    ids = (r[0] for r in form.get_release_selection())

    problems = query_longterm_problems(db,
        flatten(ids),
        form.get_component_selection())

    if "application/json" in request.META.get("HTTP_ACCEPT"):
        return HttpResponse(json.dumps(problems, cls=WebfafJSONEncoder),
                            status=200, mimetype="application/json")
    else:
        problems = paginate(problems, request)
        forward = {'problems': problems,
                   'form': form}

        return render_to_response('problems/longterm.html',
                                  forward,
                                  context_instance=RequestContext(request))


def item(request, **kwargs):
    db = pyfaf.storage.getDatabase()
    problem = db.session.query(Problem).filter(
        Problem.id == kwargs['problem_id']).first()

    if problem is None:
        raise Http404
    report_ids = [report.id for report in problem.reports]

    sub = (db.session.query(ReportOpSysRelease.opsysrelease_id,
                           func.sum(ReportOpSysRelease.count).label('cnt'))
                    .join(Report)
                    .filter(Report.id.in_(report_ids))
                    .group_by(ReportOpSysRelease.opsysrelease_id)
                    .order_by(sql.expression.desc('cnt'))
                    .subquery())

    osreleases = db.session.query(OpSysRelease, sub.c.cnt).join(sub).all()

    sub = (db.session.query(ReportArch.arch_id,
                           func.sum(ReportArch.count).label('cnt'))
                    .join(Report)
                    .filter(Report.id.in_(report_ids))
                    .group_by(ReportArch.arch_id)
                    .order_by(sql.expression.desc('cnt'))
                    .subquery())

    arches = (db.session.query(Arch, sub.c.cnt).join(sub)
                    .order_by(sql.expression.desc('cnt'))
                    .all())

    exes = (db.session.query(ReportExecutable.path,
                            func.sum(ReportExecutable.count).label('cnt'))
                    .join(Report)
                    .filter(Report.id.in_(report_ids))
                    .group_by(ReportExecutable.path)
                    .order_by(sql.expression.desc('cnt'))
                    .all())

    sub = (db.session.query(ReportPackage.installed_package_id,
                           func.sum(ReportPackage.count).label('cnt'))
                    .join(Report)
                    .filter(Report.id.in_(report_ids))
                    .group_by(ReportPackage.installed_package_id)
                    .order_by(sql.expression.desc('cnt'))
                    .subquery())
    packages_known = db.session.query(Package, sub.c.cnt).join(sub).all()

    packages_unknown = (db.session.query(ReportUnknownPackage, ReportUnknownPackage.count)
                                  .join(Report)
                                  .filter(Report.id.in_(report_ids))).all()

    packages = packages_known + packages_unknown

    packages_nevr = [(pkg.nevr(), cnt) for (pkg, cnt) in packages]

    # merge packages with different architectures
    merged_nevr = dict()
    for package, count in packages_nevr:
        if package in merged_nevr:
            merged_nevr[package] += count
        else:
            merged_nevr[package] = count

    packages_nevr = sorted(merged_nevr.items(), key=itemgetter(0, 1))

    packages_name = [(pkg.name, cnt) for (pkg, cnt) in packages]

    # merge packages with different EVRA
    merged_name = dict()
    for package, count in packages_name:
        if package in merged_name:
            merged_name[package] += count
        else:
            merged_name[package] = count

    packages_name = sorted(merged_name.items(), key=itemgetter(1), reverse=True)

    for report in problem.reports:
        for backtrace in report.backtraces:
            fid = 0
            for frame in backtrace.frames:
                fid += 1
                frame.nice_order = fid

    forward = {"problem": problem,
               "osreleases": osreleases,
               "arches": arches,
               "exes": exes,
               "packages_nevr": packages_nevr,
               "packages_name": packages_name,
               }

    return render_to_response('problems/item.html',
                            forward,
                            context_instance=RequestContext(request))

def backtraces(request):
    return render_to_response('problems/backtraces.html',
                            {},
                            context_instance=RequestContext(request))

def cluster(request):
    return render_to_response('problems/cluster.html',
                            {},
                            context_instance=RequestContext(request))

def bthash_forward(request, bthash):
    db = pyfaf.storage.getDatabase()
    db_report = get_report_by_hash(db, bthash)

    if db_report is None:
        raise Http404

    if len(db_report.backtraces) < 1:
        return render_to_response("reports/waitforit.html")

    if db_report.problem is None:
        return render_to_response("problems/waitforit.html")

    response = HttpResponse(status=302)
    response["Location"] = reverse('webfaf.problems.views.item',
                                   args=[db_report.problem.id])

    return response
