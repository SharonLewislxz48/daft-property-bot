#!/usr/bin/env python3
"""
Установка и настройка Tor для обхода блокировок
"""

import subprocess
import asyncio
import aiohttp
import json
import time

class TorInstaller:
    def __init__(self):
        self.tor_port = 9050
        self.control_port = 9051
        
    def install_tor(self):
        """Устанавливает Tor"""
        print("🔧 Устанавливаем Tor...")
        try:
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "tor"], check=True)
            print("✅ Tor установлен успешно")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки Tor: {e}")
            return False
    
    def configure_tor(self):
        """Настраивает Tor"""
        config = """
# Tor configuration for proxy
SocksPort 9050
ControlPort 9051
CookieAuthentication 1
"""
        
        try:
            with open("/tmp/torrc", "w") as f:
                f.write(config)
            
            subprocess.run([
                "sudo", "cp", "/tmp/torrc", "/etc/tor/torrc"
            ], check=True)
            
            print("✅ Tor настроен")
            return True
        except Exception as e:
            print(f"❌ Ошибка настройки Tor: {e}")
            return False
    
    def start_tor(self):
        """Запускает Tor"""
        try:
            subprocess.run(["sudo", "systemctl", "start", "tor"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "tor"], check=True)
            time.sleep(5)  # Ждем запуска
            print("✅ Tor запущен")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка запуска Tor: {e}")
            return False
    
    async def test_tor(self):
        """Тестирует Tor соединение"""
        try:
            connector = aiohttp.SocksConnector.from_url('socks5://127.0.0.1:9050')
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get('https://httpbin.org/ip') as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Tor работает! IP: {result['origin']}")
                        return True
        except Exception as e:
            print(f"❌ Tor не работает: {e}")
        
        return False
    
    async def test_daft_through_tor(self):
        """Тестирует доступ к daft.ie через Tor"""
        try:
            connector = aiohttp.SocksConnector.from_url('socks5://127.0.0.1:9050')
            timeout = aiohttp.ClientTimeout(total=15)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(
                    'https://www.daft.ie/',
                    headers=headers
                ) as response:
                    print(f"🌐 Доступ к daft.ie через Tor: {response.status}")
                    return response.status == 200
                    
        except Exception as e:
            print(f"❌ Ошибка доступа через Tor: {e}")
        
        return False

async def setup_tor():
    """Полная настройка Tor"""
    installer = TorInstaller()
    
    # Установка
    if not installer.install_tor():
        return False
    
    # Настройка
    if not installer.configure_tor():
        return False
    
    # Запуск
    if not installer.start_tor():
        return False
    
    # Тестирование
    if not await installer.test_tor():
        return False
    
    # Тест daft.ie
    if await installer.test_daft_through_tor():
        print("🎉 Tor настроен и работает с daft.ie!")
        return True
    else:
        print("⚠️ Tor работает, но daft.ie может быть заблокирован")
        return False

if __name__ == "__main__":
    print("🔧 Настройка Tor для обхода блокировок...")
    asyncio.run(setup_tor())
