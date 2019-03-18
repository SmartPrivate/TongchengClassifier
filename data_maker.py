import random
from db_handler import db_tool
from config import settings
import env
import numpy as np
import pymongo
import jieba
from tqdm import tqdm
import os


class TongChengDataSetGenerator(object):
    def __init__(self, data_table, embedding_model: env.EmbeddingModelName, user_dict='', stop_words='', balanced=False):
        """
        构造函数
        :param data_table: 数据表名称
        :param embedding_model: 采用的词嵌入模型
        :param user_dict: 用户词典文件名称（一行一个）
        :param stop_words: 停用词文件名称（一行一个）
        :param balanced: 是否对数据集进行平衡操作
        """
        self.__db_session = db_tool.Session(settings.connect_str)
        self.__mongo_session = pymongo.MongoClient(host=settings.mongo_db_host, port=settings.mongo_db_port)
        self.__user_dict = self.__load_user_words(file_name=user_dict)
        if self.__user_dict:
            jieba.load_userdict(self.__user_dict)
        self.__stop_words = self.__load_user_words(file_name=stop_words)
        self.__embedding_model = embedding_model
        self.__word2vec_collection = self.__mongo_session.tencent_ai_lab.chinese_word2vec
        self.__translate_collection = self.__mongo_session.translate_db.en_to_zh_baidu_translate
        self.__models = self.__db_session.query_all(data_table)
        if balanced:
            self.__balance_data_set()
        self.__x_list = []
        self.__y_list = []
        self.__dim = 200
        if self.__embedding_model == env.EmbeddingModelName.bert:
            self.__dim = 768

    @staticmethod
    def __load_user_words(file_name: str):
        """
        加载用户词典和停用词表
        :param file_name:
        :return:
        """
        if file_name == '':
            return None
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                words = list(map(lambda o: o.strip('\n'), lines))
                return words
        except:
            print('找不到指定文件！')
            return None

    def __word2vec_embedding(self, word=''):
        """
        词向量嵌入
        :param word: 带嵌入词（中文）
        :return: 词向量（200 dim）
        """
        result = self.__word2vec_collection.find_one({'word': word})
        if not result:
            return None
        return result['vector']

    def __translate_image_predict_label(self, word_en=''):
        """
        翻译英文标签
        :param word_en: 英文标签
        :return: 中文翻译
        """
        word_en = word_en.replace('_', ' ')
        result = self.__translate_collection.find_one({'word_en': word_en})
        if not result:
            return None
        return result['word_chn']

    def __balance_data_set(self):
        """
        数据集平衡
        :return:
        """
        helpful_guids = list(filter(lambda o: o.vote_count > 0, self.__models))
        helpful_guids = list(map(lambda o: o.guid, helpful_guids))
        helpful_guids = random.sample(helpful_guids, 5000)
        unhelpful_guids = list(filter(lambda o: o.vote_count > 0, self.__models))
        unhelpful_guids = list(map(lambda o: o.guid, unhelpful_guids))
        unhelpful_guids = random.sample(unhelpful_guids, 5000)
        guids = helpful_guids + unhelpful_guids
        self.__models = list(filter(lambda o: o.guid in guids, self.__models))

    def __get_text_feature_list(self, model):
        text_feature_array = np.zeros(self.__dim)
        word_cut_list = jieba.lcut(model.content)
        word_count = 0
        for word in word_cut_list:
            if self.__stop_words:
                if word in self.__stop_words:
                    continue
            vector = self.__word2vec_embedding(word)
            if not vector:
                continue
            vector_array = np.asarray(vector)
            text_feature_array = text_feature_array + vector_array
            word_count = word_count + 1
        if word_count:
            text_feature_array = text_feature_array / word_count
        return text_feature_array.tolist()

    def __get_image_feature_list(self, model):
        image_feature_array = np.zeros(self.__dim)
        image_predict_models = self.__db_session.query_image_prediction_by_guid(model.guid)
        image_predict_models = list(filter(lambda o: o.prob >= env.min_prob, image_predict_models))
        image_count = 0
        for image_predict_model in image_predict_models:
            word_chn = self.__translate_image_predict_label(image_predict_model.label)
            if not word_chn:
                continue
            vector = self.__word2vec_embedding(word=word_chn)
            if not vector:
                continue
            vector_array = np.asarray(vector)
            image_feature_array = image_feature_array + vector_array
            image_count = image_count + 1
        if image_count:
            image_feature_array = image_feature_array / image_count
        return image_feature_array.tolist()

    def __get_feature_vector_list(self, model):
        return [self.__get_text_feature_list(model),
                self.__get_image_feature_list(model),
                self.__get_text_length_list(model),
                self.__get_prize_list(model),
                self.__get_user_level_list(model)]

    def __get_text_length_list(self, model):
        text_length = len(model.content)
        return [text_length] * self.__dim

    def __get_prize_list(self, model):
        prize = model.prize_jiangjin
        return [prize] * self.__dim

    def __get_user_level_list(self, model):
        user_level = model.user_level
        return [user_level] * self.__dim

    @staticmethod
    def __get_vote_count(model):
        vote_count = model.vote_count
        if vote_count:
            return [1, 0]
        else:
            return [0, 1]

    def __save_feature_matrix(self, x_file_name, y_file_name):
        print('++++++正在写入npy文件++++++')
        if not os.path.exists('feature_matrix_output'):
            os.mkdir('feature_matrix_output')
        x_array = np.asarray(self.__x_list)
        y_array = np.asarray(self.__y_list)
        np.save('feature_matrix_output/{0}'.format(x_file_name), x_array)
        np.save('feature_matrix_output/{0}'.format(y_file_name), y_array)
        print('++++++数据集处理完成++++++')

    def generate_feature_matrix(self, x_file_name, y_file_name):
        for i in tqdm(range(len(self.__models)), ascii=True):
            model = self.__models[i]
            self.__x_list.append(self.__get_feature_vector_list(model))
            self.__y_list.append(self.__get_vote_count(model))
        self.__save_feature_matrix(x_file_name, y_file_name)
