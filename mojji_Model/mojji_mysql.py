import pymysql

MYSQL_HOST = 'mojji-mysql-db.cpptrs0fgqae.ap-northeast-2.rds.amazonaws.com'
MYSQL_CONN = pymysql.connect(
    host=MYSQL_HOST,
    port=3306,
    user='admin',
    passwd='k8spass#',
    db='mojji_ab',
    charset='utf8',
    cursorclass=pymysql.cursors.DictCursor
)

def conn_mysqldb():
    if not MYSQL_CONN.open:
        MYSQL_CONN.ping(reconnect=True)
    return MYSQL_CONN