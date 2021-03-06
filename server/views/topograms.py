#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask_login import login_required, current_user
from flask.ext.restful import reqparse

from server import app, restful, db
from server.models.topogram import Topogram 
from server.models.dataset import Dataset 
from server.models.regexp import Regexp

from server.forms.topogram import TopogramCreateForm
from server.serializers.topogram import TopogramSerializer
from server.serializers.dataset import DatasetSerializer

# from server.resources.socketio import send_updates

from server.lib.db_indexer import get_words_co_occurences, get_most_frequent_words, get_time_series
import pickle

class TopogramListView(restful.Resource):
    @login_required
    def get(self):
        topograms =current_user.topograms.all()
        # topograms = Topogram.query.all()
        return TopogramSerializer(topograms, many=True).data

    @login_required
    def post(self):
        form = TopogramCreateForm()

        if not form.validate_on_submit():
            return form.errors, 422

        topogram = Topogram(form.dataset_id.data, form.description.data, form.words_limit.data, form.citations_limit.data, form.stopwords.data)

        db.session.add(topogram)
        db.session.commit()

        return TopogramSerializer(topogram).data

class TopogramView(restful.Resource):

    @login_required
    def get(self, dataset_id, topogram_id):

        t = Topogram.query.filter_by(id=topogram_id).first()
        topogram= TopogramSerializer(t).data

        return topogram

    @login_required
    def delete(self, dataset_id, topogram_id):
        topogram = Topogram.query.filter_by(id=topogram_id).first()
        db.session.delete(topogram)
        db.session.commit()
        return '{"ok" : post deleted"}', 204

class TopogramsByDataset(restful.Resource):

    def get(self, id):
        print id, type(id)
        topograms = Topogram.query.filter_by(dataset_id=id).all()
        topograms = TopogramSerializer(topograms, many=True).data
        return topograms

class TopogramWordsView(restful.Resource):
    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sort', type=str, help='Sort by DB field')
        parser.add_argument('q', type=unicode, help='Search query')
        parser.add_argument('stopwords', type=unicode, help='Words to exclude')
        parser.add_argument('nodes_count', type=int, help='Max number of nodes')
        parser.add_argument('min_edge_weight', type=int, help='Min weight of graph edges ')
        self.args = parser.parse_args()

    @login_required
    def get(self, dataset_id):

        d = Dataset.query.filter_by(id=dataset_id).first()
        dataset = DatasetSerializer(d).data

        # search term
        q =self.args["q"]
        if q is not None : q.split(",")

        # stopwords
        stopwords =self.args["stopwords"]
        if stopwords is not None : stopwords = eval(stopwords)

        # 
        nodes_count = self.args["nodes_count"]
        min_edge_weight = self.args["min_edge_weight"]
        print min_edge_weight

        words = get_words_co_occurences(dataset, nodes_count=nodes_count, min_edge_weight=min_edge_weight, q=q, stopwords=stopwords)

        return words

class TopogramFrequentWordsView(restful.Resource):

    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sort', type=str, help='Sort by DB field')
        parser.add_argument('q', type=unicode, help='Search query')
        parser.add_argument('stopwords', type=unicode, help='Words to exclude')
        self.args = parser.parse_args()

    def get(self, dataset_id, words_limit):

        d = Dataset.query.filter_by(id=dataset_id).first()
        dataset = DatasetSerializer(d).data

        # search term
        q =self.args["q"]
        if q is not None : q.split(",")

        # stopwords
        stopwords =self.args["stopwords"]
        if stopwords is not None : stopwords = eval(stopwords)

        words = get_most_frequent_words(dataset, words_limit, q=q, stopwords=stopwords)

        return words

class TopogramCitationsView(restful.Resource):
    @login_required
    def get(self, topogram_id, citations_limit):

        t = Topogram.query.filter_by(id=topogram_id).first()
        topogram= TopogramSerializer(t).data

        topo = pickle.loads(topogram["networks"])

        data ={}
        data["citations"] = topo.export_citations_to_d3_js()
        data["citations"]["density"] = topo.get_citations_density()
        data["top_citations"] = topo.get_top_citations(citations_limit)

        return data

class TopogramAsCSV(restful.Resource) :
    @login_required
    def get(self, topogram_id):
        t = Topogram.query.filter_by(id=topogram_id).first()
        topogram= TopogramSerializer(t).data

class TopogramTimeSeries(restful.Resource):

    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sort', type=str, help='Sort by DB field')
        parser.add_argument('q', type=unicode, help='Search query')
        parser.add_argument('stopwords', help='Words to exclude')
        parser.add_argument('time_scale', help='Granularity of time')
        self.args = parser.parse_args()

    def get(self, dataset_id):
        d = Dataset.query.filter_by(id=dataset_id).first()
        dataset = DatasetSerializer(d).data
        
        # search term
        q =self.args["q"]
        if q is not None : q.split(",")

        # stopwords
        stopwords =self.args["stopwords"]
        if stopwords is not None : stopwords = eval(stopwords)

        # time scale
        time_scale =self.args["time_scale"]

        time_series = get_time_series(dataset, q=q, stopwords=stopwords, time_scale=time_scale)
        return time_series

class TopogramTimeFramesView(restful.Resource):
    def get(self, dataset_id, Topogram_id, start, end):
        print  start, end
        topogram = Topogram.query.filter_by(id=Topogram_id).first()
        topogram= TopogramSerializer(topogram).data
        topogram_data=mongo.db.topograms.find_one({ "_id" : ObjectId(topogram["data_mongo_id"]) })

        return timeframes_to_networks(Topogram_data)
