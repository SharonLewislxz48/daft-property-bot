#!/usr/bin/env python3
"""
Комплексная ревизия всего проекта daft-property-bot
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
import json
import time
from typing import Dict, List, Any

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

class ProjectReviewer:
    """Класс для комплексной ревизии проекта"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {}
        
    async def check_parser_functionality(self) -> Dict[str, Any]:
        """Проверка функциональности парсера"""
        print("🔍 ПРОВЕРКА ПАРСЕРА")
        print("=" * 30)
        
        results = {
            "status": "unknown",
            "tests": {},
            "performance": {},
            "issues": []
        }
        
        try:
            from production_parser import ProductionDaftParser
            
            # Тест 1: Основная функциональность
            parser = ProductionDaftParser()
            start_time = time.time()
            
            properties = await parser.search_properties(
                min_bedrooms=3,
                max_price=2500,
                location='dublin-city',
                limit=5,
                max_pages=1
            )
            
            search_time = time.time() - start_time
            
            results["tests"]["basic_search"] = {
                "passed": len(properties) > 0,
                "count": len(properties),
                "time": round(search_time, 2)
            }
            
            # Тест 2: Пагинация
            properties_multi = await parser.search_properties(
                min_bedrooms=2,
                max_price=3000,
                location='dublin-city',
                limit=20,
                max_pages=3
            )
            
            results["tests"]["pagination"] = {
                "passed": len(properties_multi) > len(properties),
                "single_page": len(properties),
                "multi_page": len(properties_multi)
            }
            
            # Тест 3: Качество данных
            if properties:
                sample_prop = properties[0]
                data_quality = {
                    "has_id": 'id' in sample_prop and sample_prop['id'],
                    "has_title": 'title' in sample_prop and sample_prop['title'],
                    "has_price": 'price' in sample_prop and sample_prop['price'] > 0,
                    "has_bedrooms": 'bedrooms' in sample_prop and sample_prop['bedrooms'] > 0,
                    "has_url": 'url' in sample_prop and sample_prop['url'].startswith('http')
                }
                
                results["tests"]["data_quality"] = {
                    "passed": all(data_quality.values()),
                    "details": data_quality
                }
            
            # Оценка производительности
            results["performance"] = {
                "search_time": round(search_time, 2),
                "properties_per_second": round(len(properties) / search_time, 1),
                "acceptable": search_time < 5
            }
            
            all_tests_passed = all(
                test.get("passed", False) 
                for test in results["tests"].values()
            )
            
            results["status"] = "success" if all_tests_passed else "partial"
            
            print(f"   ✅ Основной поиск: {len(properties)} объявлений за {search_time:.2f}с")
            print(f"   ✅ Пагинация: {len(properties_multi)} объявлений (мульти-страница)")
            print(f"   ✅ Качество данных: {all(data_quality.values())}")
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["issues"].append(f"Parser error: {e}")
            print(f"   ❌ Ошибка парсера: {e}")
        
        return results
    
    async def check_bot_components(self) -> Dict[str, Any]:
        """Проверка компонентов бота"""
        print("\n🤖 ПРОВЕРКА КОМПОНЕНТОВ БОТА")
        print("=" * 35)
        
        results = {
            "status": "unknown",
            "components": {},
            "issues": []
        }
        
        components_to_check = [
            ("bot.enhanced_bot", "EnhancedPropertyBot"),
            ("database.enhanced_database", "EnhancedDatabase"),
            ("config.regions", "ALL_LOCATIONS"),
            ("bot.enhanced_keyboards", "get_main_menu_keyboard"),
            ("bot.message_formatter", "MessageFormatter"),
            ("production_parser", "ProductionDaftParser"),
        ]
        
        successful_imports = 0
        
        for module_name, component_name in components_to_check:
            try:
                module = __import__(module_name, fromlist=[component_name])
                component = getattr(module, component_name)
                results["components"][f"{module_name}.{component_name}"] = "success"
                print(f"   ✅ {module_name}.{component_name}")
                successful_imports += 1
            except Exception as e:
                results["components"][f"{module_name}.{component_name}"] = f"failed: {e}"
                results["issues"].append(f"Import error {module_name}.{component_name}: {e}")
                print(f"   ❌ {module_name}.{component_name}: {e}")
        
        results["status"] = "success" if successful_imports == len(components_to_check) else "partial"
        results["success_rate"] = f"{successful_imports}/{len(components_to_check)}"
        
        return results
    
    def check_project_structure(self) -> Dict[str, Any]:
        """Проверка структуры проекта"""
        print("\n📁 ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
        print("=" * 40)
        
        results = {
            "status": "unknown",
            "files": {},
            "issues": []
        }
        
        critical_files = [
            "production_parser.py",
            "bot/enhanced_bot.py",
            "database/enhanced_database.py",
            "config/regions.py",
            "requirements.txt",
            "README.md"
        ]
        
        optional_files = [
            ".env.example",
            "bot_config.json",
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        existing_critical = 0
        existing_optional = 0
        
        print("   📋 Критические файлы:")
        for file_path in critical_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            results["files"][file_path] = "exists" if exists else "missing"
            
            if exists:
                existing_critical += 1
                print(f"      ✅ {file_path}")
            else:
                print(f"      ❌ {file_path}")
                results["issues"].append(f"Missing critical file: {file_path}")
        
        print("   📋 Дополнительные файлы:")
        for file_path in optional_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            results["files"][file_path] = "exists" if exists else "missing"
            
            if exists:
                existing_optional += 1
                print(f"      ✅ {file_path}")
            else:
                print(f"      ⚠️ {file_path}")
        
        results["critical_files"] = f"{existing_critical}/{len(critical_files)}"
        results["optional_files"] = f"{existing_optional}/{len(optional_files)}"
        results["status"] = "success" if existing_critical == len(critical_files) else "partial"
        
        return results
    
    def check_configuration(self) -> Dict[str, Any]:
        """Проверка конфигурации"""
        print("\n⚙️ ПРОВЕРКА КОНФИГУРАЦИИ")
        print("=" * 30)
        
        results = {
            "status": "unknown",
            "configs": {},
            "issues": []
        }
        
        # Проверка bot_config.json
        bot_config_path = self.project_root / "bot_config.json"
        if bot_config_path.exists():
            try:
                with open(bot_config_path, 'r', encoding='utf-8') as f:
                    bot_config = json.load(f)
                
                required_keys = ["default_search", "bot_settings"]
                config_valid = all(key in bot_config for key in required_keys)
                
                results["configs"]["bot_config"] = "valid" if config_valid else "invalid"
                print(f"   ✅ bot_config.json: валидный" if config_valid else "   ❌ bot_config.json: невалидный")
                
            except Exception as e:
                results["configs"]["bot_config"] = f"error: {e}"
                results["issues"].append(f"bot_config.json error: {e}")
                print(f"   ❌ bot_config.json: ошибка {e}")
        else:
            results["configs"]["bot_config"] = "missing"
            print("   ⚠️ bot_config.json: отсутствует")
        
        # Проверка .env
        env_path = self.project_root / ".env"
        env_example_path = self.project_root / ".env.example"
        
        if env_path.exists():
            results["configs"]["env_file"] = "exists"
            print("   ✅ .env: существует")
        elif env_example_path.exists():
            results["configs"]["env_file"] = "example_only"
            print("   ⚠️ .env: только пример (.env.example)")
        else:
            results["configs"]["env_file"] = "missing"
            results["issues"].append("No .env or .env.example file found")
            print("   ❌ .env: отсутствует")
        
        results["status"] = "success" if not results["issues"] else "partial"
        return results
    
    async def check_integration(self) -> Dict[str, Any]:
        """Проверка интеграции между компонентами"""
        print("\n🔗 ПРОВЕРКА ИНТЕГРАЦИИ")
        print("=" * 30)
        
        results = {
            "status": "unknown",
            "integrations": {},
            "issues": []
        }
        
        try:
            # Тест интеграции парсера с ботом
            from production_parser import ProductionDaftParser
            
            # Симуляция вызова из бота
            parser = ProductionDaftParser()
            bot_settings = {
                "regions": ["dublin-city"],
                "min_bedrooms": 3,
                "max_price": 2500,
                "max_results_per_search": 5
            }
            
            # Тест как в реальном боте
            region_results = await parser.search_properties(
                min_bedrooms=bot_settings["min_bedrooms"],
                max_price=bot_settings["max_price"],
                location=bot_settings["regions"][0],
                limit=bot_settings["max_results_per_search"]
            )
            
            integration_success = len(region_results) > 0
            results["integrations"]["parser_bot"] = "success" if integration_success else "failed"
            
            print(f"   {'✅' if integration_success else '❌'} Парсер ↔ Бот: {len(region_results)} объявлений")
            
            if not integration_success:
                results["issues"].append("Parser-Bot integration failed")
            
        except Exception as e:
            results["integrations"]["parser_bot"] = f"error: {e}"
            results["issues"].append(f"Integration test error: {e}")
            print(f"   ❌ Интеграция: ошибка {e}")
        
        results["status"] = "success" if not results["issues"] else "failed"
        return results
    
    def generate_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация итогового резюме"""
        summary = {
            "overall_status": "unknown",
            "readiness": "unknown",
            "critical_issues": [],
            "recommendations": [],
            "statistics": {}
        }
        
        # Подсчет успешных компонентов
        successful_components = 0
        total_components = 0
        
        for category, result in all_results.items():
            if result.get("status") == "success":
                successful_components += 1
            total_components += 1
        
        success_rate = successful_components / total_components if total_components > 0 else 0
        
        # Сбор критических проблем
        for category, result in all_results.items():
            if "issues" in result:
                summary["critical_issues"].extend(result["issues"])
        
        # Определение общего статуса
        if success_rate >= 0.8:
            summary["overall_status"] = "excellent"
            summary["readiness"] = "production_ready"
        elif success_rate >= 0.6:
            summary["overall_status"] = "good"
            summary["readiness"] = "mostly_ready"
        elif success_rate >= 0.4:
            summary["overall_status"] = "partial"
            summary["readiness"] = "needs_fixes"
        else:
            summary["overall_status"] = "poor"
            summary["readiness"] = "not_ready"
        
        # Рекомендации
        if len(summary["critical_issues"]) == 0:
            summary["recommendations"].append("✅ Проект готов к продакшену")
            summary["recommendations"].append("🚀 Можно деплоить на сервер")
        else:
            summary["recommendations"].append("🔧 Исправить критические проблемы")
            if any("parser" in issue.lower() for issue in summary["critical_issues"]):
                summary["recommendations"].append("🔍 Проверить функциональность парсера")
            if any("import" in issue.lower() for issue in summary["critical_issues"]):
                summary["recommendations"].append("📦 Проверить зависимости и импорты")
        
        # Статистика
        summary["statistics"] = {
            "success_rate": f"{success_rate:.1%}",
            "successful_components": f"{successful_components}/{total_components}",
            "critical_issues_count": len(summary["critical_issues"])
        }
        
        return summary
    
    async def run_full_review(self):
        """Запуск полной ревизии проекта"""
        print("🔍 КОМПЛЕКСНАЯ РЕВИЗИЯ ПРОЕКТА daft-property-bot")
        print("=" * 60)
        
        # Настройка логирования
        logging.basicConfig(level=logging.ERROR)  # Только ошибки
        
        # Запуск всех проверок
        parser_results = await self.check_parser_functionality()
        bot_results = await self.check_bot_components()
        structure_results = self.check_project_structure()
        config_results = self.check_configuration()
        integration_results = await self.check_integration()
        
        all_results = {
            "parser": parser_results,
            "bot_components": bot_results,
            "project_structure": structure_results,
            "configuration": config_results,
            "integration": integration_results
        }
        
        # Генерация резюме
        summary = self.generate_summary(all_results)
        
        # Вывод итогового резюме
        print("\n" + "=" * 60)
        print("📊 ИТОГОВОЕ РЕЗЮМЕ ПРОЕКТА")
        print("=" * 60)
        
        print(f"🎯 Общий статус: {summary['overall_status'].upper()}")
        print(f"🚀 Готовность: {summary['readiness'].replace('_', ' ').upper()}")
        print(f"📈 Успешность: {summary['statistics']['success_rate']}")
        print(f"📊 Компоненты: {summary['statistics']['successful_components']}")
        
        if summary["critical_issues"]:
            print(f"\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(summary['critical_issues'])}):")
            for issue in summary["critical_issues"][:5]:  # Показываем первые 5
                print(f"   • {issue}")
        else:
            print("\n✅ КРИТИЧЕСКИХ ПРОБЛЕМ НЕТ")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for rec in summary["recommendations"]:
            print(f"   • {rec}")
        
        # Детальные результаты
        print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for category, result in all_results.items():
            status_emoji = "✅" if result.get("status") == "success" else "⚠️" if result.get("status") == "partial" else "❌"
            print(f"   {status_emoji} {category.replace('_', ' ').title()}: {result.get('status', 'unknown')}")
        
        self.results = {
            "summary": summary,
            "detailed_results": all_results,
            "timestamp": time.time()
        }
        
        return self.results

async def main():
    """Основная функция ревизии"""
    reviewer = ProjectReviewer()
    results = await reviewer.run_full_review()
    
    # Сохранение результатов
    results_file = Path(__file__).parent / "project_review_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Результаты сохранены в: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
