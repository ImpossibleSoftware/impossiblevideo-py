import os
import urllib
import requests
from requests.auth import HTTPBasicAuth

import json

from iv import IIO_DEFAULT_HOST, IIO_DEFAULT_RENDERER
from iv.proto import Movie




class Renderer:
    def __init__(self, project, moviename, endpoint=IIO_DEFAULT_RENDERER):
        self.project = project
        self.moviename = moviename
        self.endpoint = endpoint
        self.http = httplib2.Http()

    def action(self, _action, extension, **kwargs):
        url = "%s/v1/%s/%s/%s.%s" % (self.endpoint, _action, self.project.project_uid, self.moviename, extension)
        if kwargs is not None:
            url += "?" + urllib.urlencode(kwargs)

        r = self.http.request(url, "GET")
        if r.status_code != 200:
            raise RuntimeError("Failed rendering %s: %s" % (url, r.text))

        return r.text

    def render(self, extension, **kwargs):
        return self.action("render", extension, **kwargs)

    def get(self, extension, **kwargs):
        return self.action("get", extension, **kwargs)

    def galaxy(self, extension, **kwargs):
        return self.action("galaxy", extension, **kwargs)


class DynamicMovieVariable:
    def __init__(self, dynamicmovie, **kwargs):
        self.project = dynamicmovie.project
        self.movie = dynamicmovie
        self.defaultvalue = kwargs.get('defaultvalue', None)
        self.name = kwargs.get('name', None)
        self.offset = kwargs.get('offset', None)
        self.numframes = kwargs.get('numframes', None)
        self.type = kwargs.get('type', None)

    def __repr__(self):
        return "DynamicMovie(%r, %s)" % (self.project, self.name)

    def __str__(self):
        return "DynamicMovieVariable '%s' (movie=%s, project=%s)" % (self.name, self.movie, self.project.name)



class DynamicMovie:
    def __init__(self, project, name):
        self.project = project
        self.name = name

    def __repr__(self):
        return "DynamicMovie(%r, %s)" % (self.project, self.name)

    def __str__(self):
        return "DynamicMovie '%s' (project=%s (%s))" % (self.name, self.project.name, self.project.project_uid)

    def get_movie(self, abspath=False):
        return self.project.get_dynamic_movie(self.name, abspath)

    def list_variables(self):
        uri = "/v1/sdlvariables/%s/%s" % (self.project.project_uid, self.name)
        r = self.project.connection.request(uri, "GET")
        if r.status_code not in [200, 201]:
            raise RuntimeError("Unable to retrieve variable info for '%s': " % (self.name, r.text))

        result = json.loads(r.text)
        return [DynamicMovieVariable(self, **data) for data in result['variables']]

    def delete(self):
        uri = "/v1/sdl/%s/%s" % (self.project.project_uid, self.name)
        r = self.project.connection.request(uri, "DELETE")
        if r.status_code not in [200, 201]:
            raise RuntimeError("Unable to delete '%s': " % (self.name, r.text))


class PublishedProject:

    def __init__(self, project_uid=None, project_name=None):
        self.project_uid = project_uid
        self.name = project_name

class Project:
    def __init__(self, connection, project_uid=None, project_name=None):
        self.connection = connection
        self.project_uid = project_uid
        self.name = project_name

    def __repr__(self):
        return "Project(%r, %s, %s)" % (self.connection, self.project_uid, self.name)

    def __str__(self):
        return "Project '%s' (uid='%s')" % (self.name, self.project_uid)

    def publish(self, location):
        uri = "/v1/publish/%s/%s" % (self.project_uid, location)
        r = self.connection.request(uri, "POST")
        if r.status_code not in [200, 201]:
            raise RuntimeError("Project %s (%s) cannot be published: %s" % (self.name, self.project_uid, r.text))
        if r.status_code in [200, 201]:
            result = json.loads(r.text)
            return PublishedProject(result.get("Published-UID", self.project_uid), self.name)


    def destroy(self):
        uri = "/v1/project/%s" % self.project_uid
        r = self.connection.request(uri, "DELETE")
        if r.status_code not in [200, 201]:
            raise RuntimeError("Project %s (%s) cannot be destroyed: %s" % (self.name, self.project_uid, r.text))

    def list_dynamic_movies(self):
        uri = "/v1/list/sdl/%s" % (self.project_uid)
        r = self.connection.request(uri, "GET")
        if r.status_code not in [200, 201]:
            raise RuntimeError("Cannot list dynamic movies from project %s: %s" % (self.project_uid, r.text))
        if r.status_code == 200:
            result = json.loads(r.text)
            return [DynamicMovie(self, s) for s in result['SDLS']]

    def create_dynamic_movie(self, movie, moviename, preencode=True, normalize=True):
#       uri = "/v1/sdl/%s/%s" % (self.project_uid, moviename)
        nopreencode = 0 if preencode else 1
        nonormalize = 0 if normalize else 1

        uri = "/v1/sdl/%s/%s?nonormalize=%d&nopreencode=%d" % (self.project_uid, moviename, nonormalize, nopreencode)
        print uri
        ms = movie.SerializeToString()
        r = self.connection.request(uri, "POST", body=bytes(ms), headers={'content-type':'application/octet-stream'})
        if r.status_code not in [200, 201]:
            raise RuntimeError("Dynamic movie %s from project %s not created: %s" % (moviename, self.project_uid, r.text))
        dmovie = DynamicMovie(self, moviename)
        return dmovie

    def debug_dynamic_movie(self, movie, moviename):
        uri = "/v1/sdlmovieerrors/%s/%s" % (self.project_uid, moviename)
        ms = movie.SerializeToString()
        r = self.connection.request(uri, "GET", headers={'content-type':'application/octet-stream'})
        print r.text

    def get_dynamic_movie(self, moviename, abspath=False):
        uri = "/v1/sdl/%s/%s?notprojectspecific=%s" % (self.project_uid, moviename, str(abspath))
        header, content = self.connection.request(uri, "GET")
        if r.status_code not in [200, 201]:
            raise RuntimeError("Dynamic movie %s from project %s not loaded: %s" % (moviename, self.project_uid, r.text))
        movie = Movie()
        movie.ParseFromString(r.content)
        return movie

    def upload_file(self, f, filename=None, mimetype=None):
        headers = {'content-type': 'application/octet-stream'}

        if not filename:
            if not f.name:
                raise RuntimeError("No filename given")
            filename = f.name   

        uri = "/v1/data/%s/%s" % (self.project_uid, filename)
        if mimetype:
            headers.update({'content-type': mimetype})

        fileno = f.fileno()
        stats = os.fstat(fileno)
        headers.update({'content-length': str(stats.st_size)})

        r = self.connection.request(uri, "PUT", body=f, headers=headers)
        if r.status_code not in [200, 201]:
            raise RuntimeError("File %s cannot be uploaded to project %s: %s" % (filename, self.project_uid, r.text))
        return json.loads(r.text)['Resource-Name']

    def delete_file(self, filename):
        uri = "/v1/data/%s/%s" % (self.project_uid, filename)
        r = self.connection.request(uri, "DELETE")
        if r.status_code not in [200, 201]:
            raise RuntimeError("File %s cannot be deleted from project %s: %s" % (filename, self.project_uid, r.text))

    def get_file(self, filename):
        uri = "/v1/data/%s/%s" % (self.project_uid, filename)
        r = self.connection.request(uri, "GET")
        if r.status_code not in [200, 201]:
            raise RuntimeError("File %s cannot be fetched from project %s" % (filename, self.project_uid, r.text))
        return r.content

    def list_files(self):
        uri = "/v1/list/data/%s" % (self.project_uid)
        r = self.connection.request(uri, "GET")
        if r.status_code not in [200, 201]:
            raise RuntimeError("Cannot list files from project %s: %s" % (self.project_uid, r.text))
        result = json.loads(r.text)
        return result

class Connection:

    def __init__(self, credentials_key, credentials_pass, host=IIO_DEFAULT_HOST):
        self.session = requests.Session()
        self.auth = HTTPBasicAuth(credentials_key, credentials_pass)
        self._host = host

    def __repr__(self):
        return "Connection(%s, %s, %s)" % (self.credentials_key, self.credentials_pass, self._host)

    def __str__(self):
        return "IIO Connection to %s as user '%s'" % (self._host, self.credentials_key)


    def request(self, uri, method, body=None, headers=None):
        url = "%s%s" % (self._host, uri)
        r = self.session.request(method, url, data=body, headers=headers, auth=self.auth)
        return r

    def list_projects(self):
        uri = "/v1/list/project"
        r = self.request(uri, "GET")
        if r.status_code not in [200, 201]:
            raise Exception(r.text)

        result = json.loads(r.content)
        return [Project(self, p[0], p[1]) for p in result['Projects']]

    def create_project(self, project_name):
        uri = "/v1/project/%s" % project_name
        r = self.request(uri, "POST")

        if r.status_code not in [200, 201]:
            raise RuntimeError("Project %s cannot be created: %s" % (project_name, r.text))
        return Project(self, json.loads(r.content)['Project-UID'], project_name)

    def get_project_byname(self, project_name):
        prjs = self.list_projects()
        for p in prjs:
            if p.name == project_name:
                return p
        return None

    def get_project_byuid(self, uid):
        prjs = self.list_projects()
        for p in prjs:
            if p.project_uid == uid:
                return p
        return None

    def get_or_create_project(self, project_name):
        prjs = self.list_projects()
        for p in prjs:
            if p.name == project_name:
                return p

        return self.create_project(project_name)


