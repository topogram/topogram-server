#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.resources import app
from flask.ext.elasticsearch import ElasticSearch

# elastic search
elastic = ElasticSearch(app)

