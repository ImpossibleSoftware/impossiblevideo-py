#!/usr/bin/env python2

import os
import sys
import json
import argparse
import ConfigParser

from iv.api import Connection, Project, Renderer

IVCFGNAMEETC = "iv.cfg"
IVCFGNAMEHOME = ".iv"
IVCFGNAMEPROJECT = "config.ini"

def get_config():
    cwd = os.getcwd()
    config = os.path.join(cwd, IVCFGNAMEPROJECT)
    cp = ConfigParser.ConfigParser()
    cp.read(config)
    return cp

def get_project_uid():
    cp = get_config()
    key = cp.get("project", "project_uid")
    return key


def get_connection(args):
    # Try args, environment, ~/.iv.cfg, /etc/iv.cfg

    envkey = os.environ.get('IV_APIKEY')
    envsecret = os.environ.get('IV_APISECRET')

    if args.key and args.secret:
        return  Connection(args.key, args.secret)
    elif envkey and envsecret:
        return Connection(envkey, envsecret)
    else:
        cp = ConfigParser.ConfigParser()
        filenames = (
            os.path.join(os.getcwd(), IVCFGNAMEPROJECT),
            os.path.join(os.environ['HOME'], IVCFGNAMEHOME),
            os.path.join("/etc", IVCFGNAMEETC)
        )
        for filename in filenames:
            try:
                cp.read(filename)
                return Connection(cp.get("auth", "apikey"), cp.get("auth", "apisecret"))
            except Exception, e:
                pass

    raise RuntimeError("No API key and secret found")


def create(args):
    c = get_connection(args)
 
    p = c.create_project(args.name)

    try:
        os.mkdir(args.name)
    except:
        if not args.force:
            raise RuntimeError("Project Directory already exists. Use -f to force")

    try:
        os.mkdir(os.path.join(args.name, "userdata"))   
    except:
        if not args.force:
            raise RuntimeError("Project userdata already exists. Use -f to force")

    config = os.path.join(args.name, "config.ini")
    with open(config, "w") as f:
        f.write("[auth]\n")
        f.write("apikey=%s\n" % c.credentials_key)
        f.write("apisecret=%s\n" % c.credentials_pass)
        f.write("[project]\n")
        f.write("name=%s\n" % args.name)
        f.write("project_uid=%s\n" % p.project_uid)

    print "Created Project %s with UUID %s" % (p.name, p.project_uid)

def destroy(args):
    c = get_connection(args)

    if(args.uid):
        p = c.get_project_byuid(args.uid)
        if not p:
            raise RuntimeError("Project not found")
        p.destroy()
    if(args.name):
        p = c.get_project_byname(args.name)
        if not p:
            raise RuntimeError("Project not found")
        p.destroy()

    print "Project destroyed on server."


def upload(args):
    c = get_connection(args)
    project_uid = get_project_uid()
    p = c.get_project_byuid(project_uid)
    print "Uploading..."
    resource_name = p.upload_file(args.infile, os.path.basename(args.infile.name), args.mimetype)
    print "File uploaded as:", resource_name

def delete(args):
    c = get_connection(args)
    project_uid = get_project_uid()
    p = c.get_project_byuid(project_uid)
    p.delete_file(args.name)
    print "File deleted on server"


def list_wrapper(args):
    c = get_connection(args)
    project_uid = get_project_uid()
    p = c.get_project_byuid(project_uid)
    data = p.list_files()
    print json.dumps(data, indent=4, separators=(',', ': '))

def push(args):
    c = get_connection(args)
    project_uid = get_project_uid()
    p = c.get_project_byuid(project_uid)
    module, var = args.module_var.split(':')

    import sys
    sys.path.append('.')
    mod = __import__(module)
    movie = getattr(mod, var)
    p.create_dynamic_movie(movie, var)
    print "Dynamic movie uploaded"

def publish(args):
    print("publish", args)

def render(args):
    c = get_connection(args)
    project_uid = get_project_uid()
    p = c.get_project_byuid(project_uid)
    r = Renderer(p, args.movie)

    kwargs = {x.split('=')[0]:x.split('=')[1] for x in args.args}
    content = r.render(args.format, **kwargs)

    if args.outfile:
        args.outfile.write(content)
        print "Movie rendered and saved as", args.outfile.name
    else:
        with open(args.movie + "." + args.format, "wb") as f:
            f.write(content)
            print "Movie rendered and saved as", f.name




parser = argparse.ArgumentParser()
parser.add_argument('-k', '--key', default=None, help="API key")
parser.add_argument('-s', '--secret', default=None, help="API secret")


subparsers = parser.add_subparsers()


parser_create = subparsers.add_parser('create')
parser_create.add_argument('-f', '--force', action='store_true', default=False, help="Force project creation")
parser_create.add_argument('name', help="Name of project")
parser_create.set_defaults(func=create)


parser_destroy = subparsers.add_parser('destroy')
group = parser_destroy.add_mutually_exclusive_group(required=True)
group.add_argument('--uid', help="UID of project")
group.add_argument('--name', help="name of project")
parser_destroy.set_defaults(func=destroy)


parser_upload = subparsers.add_parser('upload')
parser_upload.add_argument('--mimetype', default=None)
parser_upload.add_argument('infile', type=argparse.FileType('r'))
parser_upload.set_defaults(func=upload)


parser_delete = subparsers.add_parser('delete')
parser_delete.add_argument('name', default= None, help="Name of resource to be deleted")
parser_delete.set_defaults(func=delete)


parser_list = subparsers.add_parser('list')
parser_list.set_defaults(func=list_wrapper)


parser_push = subparsers.add_parser('push')
parser_push.add_argument('module_var')
parser_push.set_defaults(func=push)

parser_publish = subparsers.add_parser('publish')
parser_publish.set_defaults(func=publish)

parser_render = subparsers.add_parser('render')
parser_render.add_argument('--format', default="mp4")
parser_render.add_argument('-o', '--outfile', type=argparse.FileType('wb'), help="output filename")
parser_render.add_argument('movie')
parser_render.add_argument('args', nargs='*')
parser_render.set_defaults(func=render)

args = parser.parse_args()
args.func(args)

