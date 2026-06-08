"""
API Service Module
ដេលីវើរីបត់សេវាកម្ម API សម្រាប់ប្រើប្រាស់ក្នុងប្រអប់ Telegram និងសេវាកម្មផ្សេងទៀត
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from aiohttp import ClientSession, ClientError, web
from config.settings import get_db_connection, execute_query

logger = logging.getLogger(__name__)


class APIService:
    """
    Main API Service class for handling HTTP requests and API communications
    ថ្នាក់សេវាកម្ម API សម្រាប់គ្រប់គ្រងសំណើ HTTP និងការរឹងរឹងសារ
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize API Service
        
        Args:
            timeout (int): Request timeout in seconds
        """
        self.timeout = timeout
        self.session: Optional[ClientSession] = None
    
    async def init_session(self):
        """Initialize aiohttp ClientSession"""
        if not self.session:
            self.session = ClientSession()
            logger.info("✅ API Service session initialized")
    
    async def close_session(self):
        """Close aiohttp ClientSession"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("✅ API Service session closed")
    
    async def get(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request
        
        Args:
            url (str): URL to request
            headers (dict): Optional headers
            params (dict): Optional query parameters
            
        Returns:
            dict: Response data
        """
        try:
            await self.init_session()
            async with self.session.get(
                url, 
                headers=headers, 
                params=params,
                timeout=self.timeout
            ) as response:
                data = await response.json()
                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "data": data
                }
        except asyncio.TimeoutError:
            logger.error(f"⏱️ GET Request timeout: {url}")
            return {"success": False, "error": "Request timeout"}
        except ClientError as e:
            logger.error(f"❌ GET Request error: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Unexpected error in GET: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def post(
        self, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: bool = True
    ) -> Dict[str, Any]:
        """
        Make POST request
        
        Args:
            url (str): URL to request
            data (dict): Request data
            headers (dict): Optional headers
            json_data (bool): Send as JSON (default True)
            
        Returns:
            dict: Response data
        """
        try:
            await self.init_session()
            kwargs = {"timeout": self.timeout}
            if headers:
                kwargs["headers"] = headers
            
            if json_data:
                kwargs["json"] = data
            else:
                kwargs["data"] = data
            
            async with self.session.post(url, **kwargs) as response:
                response_data = await response.json()
                return {
                    "success": response.status in [200, 201],
                    "status": response.status,
                    "data": response_data
                }
        except asyncio.TimeoutError:
            logger.error(f"⏱️ POST Request timeout: {url}")
            return {"success": False, "error": "Request timeout"}
        except ClientError as e:
            logger.error(f"❌ POST Request error: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Unexpected error in POST: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def put(
        self, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make PUT request
        
        Args:
            url (str): URL to request
            data (dict): Request data
            headers (dict): Optional headers
            
        Returns:
            dict: Response data
        """
        try:
            await self.init_session()
            async with self.session.put(
                url, 
                json=data,
                headers=headers,
                timeout=self.timeout
            ) as response:
                response_data = await response.json()
                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "data": response_data
                }
        except Exception as e:
            logger.error(f"❌ PUT Request error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def delete(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make DELETE request
        
        Args:
            url (str): URL to request
            headers (dict): Optional headers
            
        Returns:
            dict: Response data
        """
        try:
            await self.init_session()
            async with self.session.delete(
                url, 
                headers=headers,
                timeout=self.timeout
            ) as response:
                response_data = await response.json()
                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "data": response_data
                }
        except Exception as e:
            logger.error(f"❌ DELETE Request error: {str(e)}")
            return {"success": False, "error": str(e)}


class DatabaseService:
    """
    Database Service for handling database operations
    សេវាកម្មមូលដ្ឋានទិន្នន័យសម្រាប់គ្រប់គ្រងការដំណើរការលើមូលដ្ឋានទិន្នន័យ
    """
    
    @staticmethod
    def execute_query(sql: str, params: tuple = None) -> Dict[str, Any]:
        """
        Execute a database query
        
        Args:
            sql (str): SQL query
            params (tuple): Query parameters
            
        Returns:
            dict: Query result
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_query(cursor, sql, params or ())
            conn.commit()
            cursor.close()
            conn.close()
            return {"success": True, "message": "Query executed successfully"}
        except Exception as e:
            logger.error(f"❌ Database query error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def fetch_one(sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Fetch one record from database
        
        Args:
            sql (str): SQL query
            params (tuple): Query parameters
            
        Returns:
            dict: Single record or None
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_query(cursor, sql, params or ())
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"❌ Fetch one error: {str(e)}")
            return None
    
    @staticmethod
    def fetch_all(sql: str, params: tuple = None) -> List[Any]:
        """
        Fetch all records from database
        
        Args:
            sql (str): SQL query
            params (tuple): Query parameters
            
        Returns:
            list: All matching records
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_query(cursor, sql, params or ())
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"❌ Fetch all error: {str(e)}")
            return []
    
    @staticmethod
    def insert(sql: str, params: tuple = None) -> Optional[int]:
        """
        Insert record into database
        
        Args:
            sql (str): SQL query
            params (tuple): Query parameters
            
        Returns:
            int: Last insert ID or None
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_query(cursor, sql, params or ())
            last_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            return last_id
        except Exception as e:
            logger.error(f"❌ Insert error: {str(e)}")
            return None
    
    @staticmethod
    def update(sql: str, params: tuple = None) -> int:
        """
        Update records in database
        
        Args:
            sql (str): SQL query
            params (tuple): Query parameters
            
        Returns:
            int: Number of affected rows
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_query(cursor, sql, params or ())
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return affected
        except Exception as e:
            logger.error(f"❌ Update error: {str(e)}")
            return 0
    
    @staticmethod
    def delete(sql: str, params: tuple = None) -> int:
        """
        Delete records from database
        
        Args:
            sql (str): SQL query
            params (tuple): Query parameters
            
        Returns:
            int: Number of deleted rows
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            execute_query(cursor, sql, params or ())
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return affected
        except Exception as e:
            logger.error(f"❌ Delete error: {str(e)}")
            return 0


# Initialize global service instances
api_service = APIService()
db_service = DatabaseService()


async def start_api_service():
    """Start API service and initialize session"""
    await api_service.init_session()
    logger.info("🚀 API Service started")


async def stop_api_service():
    """Stop API service and close session"""
    await api_service.close_session()
    logger.info("🛑 API Service stopped")
