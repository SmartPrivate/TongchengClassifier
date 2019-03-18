from db_handler import orm_models
import data_maker
import env

user_dict_dir = 'dict_files/user_dict.csv'
stop_words_dir = 'dict_files/stop_words.txt'

generator = data_maker.TongChengDataSetGenerator(orm_models.VCommentDetailWithPic,
                                                 embedding_model=env.EmbeddingModelName.word2vec, user_dict=user_dict_dir,
                                                 stop_words=stop_words_dir, balanced=False)

generator.generate_feature_matrix(x_file_name='x.npy', y_file_name='y.npy')
