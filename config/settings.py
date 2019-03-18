import configparser

cf = configparser.ConfigParser()
cf.read('../config.ini')

# 数据库连接串
connect_str: str = cf.get('CentOS_MySQL', 'connect_str')

# mongo_db配置
mongo_db_host: str = cf.get('CentOS_MongoDB', 'host')
mongo_db_port: int = int(cf.get('CentOS_MongoDB', 'port'))
