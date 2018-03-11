# -*- coding=utf-8 -*-
'''
应用基类（每次应用启动时，都必须调用基类的初始化方法）
@author: welliam.cao<303350019@qq.com> 
@version:1.0 2017年4月12日
'''
import redis
from django.conf import settings
import MySQLdb  
from MySQLdb.cursors import DictCursor  
from DBUtils.PooledDB import PooledDB  


class APBase(object):
    REDSI_POOL = 10000
    MYSQL_POOLS = dict()
    
    @staticmethod
    def getRedisConnection(db):
        '''根据数据源标识获取Redis连接池'''
        if db==APBase.REDSI_POOL:
            args = settings.REDSI_KWARGS_LPUSH
            if settings.REDSI_LPUSH_POOL == None:
                settings.REDSI_LPUSH_POOL = redis.ConnectionPool(host=args.get('host'), port=args.get('port'), db=args.get('db'))
            pools = settings.REDSI_LPUSH_POOL  
        connection = redis.Redis(connection_pool=pools)
        return connection

   
class MySQLPool(APBase): 
    def __init__(self,host,port,user,passwd,dbName,):
        self.poolKeys = host+dbName+str(port)
        if self.poolKeys not in MySQLPool.MYSQL_POOLS.keys():  
            self._conn = self._getTupleConn(host,port,user,passwd,dbName)  
            MySQLPool.MYSQL_POOLS[self.poolKeys] = self._conn
        self._conn = MySQLPool.MYSQL_POOLS.get(self.poolKeys)
        if not isinstance(self._conn,str):self._cursor = self._conn.cursor()          
 
    def _getDictConn(self,host,port,user,passwd,dbName):
        '''返回字典类型结果集'''   
        if APBase.MYSQL_POOLS.get(self.poolKeys) is None:
            try:
                pool = PooledDB(creator=MySQLdb, mincached=1 , maxcached=20 ,  
                                      host=host , port=port , user=user , passwd=passwd ,  
                                      db=dbName,use_unicode=False,charset='utf8',
                                      cursorclass=DictCursor)  
                APBase.MYSQL_POOLS[self.poolKeys] = pool   
                return APBase.MYSQL_POOLS.get(self.poolKeys).connection()  
            except Exception, ex:
                return str(ex)
            
    def _getTupleConn(self,host,port,user,passwd,dbName):
        '''返回列表类型结果集'''   
        if APBase.MYSQL_POOLS.get(self.poolKeys) is None:
            try:
                pool = PooledDB(creator=MySQLdb, mincached=1 , maxcached=20 ,  
                                      host=host , port=port , user=user , passwd=passwd ,  
                                      db=dbName,use_unicode=False,charset='utf8')  
                APBase.MYSQL_POOLS[self.poolKeys] = pool   
                return APBase.MYSQL_POOLS.get(self.poolKeys).connection()  
            except Exception, ex:
                return str(ex)
   
    def queryAll(self,sql):
        if isinstance(self._conn,str):return self._conn   
        try: 
            count = self._cursor.execute(sql)   
            result = self._cursor.fetchall()   
            return (count,result)  
        except Exception,ex:
            return str(ex)

   
    def queryOne(self,sql):  
        if isinstance(self._conn,str):return self._conn 
        try: 
            count = self._cursor.execute(sql)   
            result = self._cursor.fetchone()   
            return (count,result)  
        except Exception,ex:
            return str(ex)

  
   
    def queryMany(self,sql,num,param=None):
        if isinstance(self._conn,str):return self._conn   
        """ 
        @summary: 执行查询，并取出num条结果 
        @param sql:查询ＳＱＬ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来 
        @param num:取得的结果条数 
        @return: result list/boolean 查询到的结果集 
        """  
        try:
            count = self._cursor.execute(sql,param)  
            index = self._cursor.description
            colName = []
            for i in index:
                colName.append(i[0])            
            result = self._cursor.fetchmany(size=num) 
            return (count,result,colName) 
        except Exception,ex:
            return str(ex)   
    
    def execute(self,sql,num=1000):
        if isinstance(self._conn,str):return self._conn 
        try:
            count = self._cursor.execute(sql)
            index = self._cursor.description
            colName = []
            if index:
                for i in index:
                    colName.append(i[0]) 
            result = self._cursor.fetchmany(size=num)           
            self._conn.commit()
            return (count,result,colName) 
        except Exception, ex:
            return str(ex)


   
    def close(self,isEnd=1):  
        """ 
        @summary: 释放连接池资源 
        """  
        try:
            self._cursor.close()  
            self._conn.close() 
        except:
            pass