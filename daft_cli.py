#!/usr/bin/env python3
"""
CLI интерфейс для продакшн парсера daft.ie
"""

import argparse
import asyncio
import sys
from production_daft_parser import ProductionDaftParser

def create_parser():
    """Создает парсер аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Парсер недвижимости daft.ie',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python daft_cli.py --min-bedrooms 3 --max-price 2500 --location dublin
  python daft_cli.py --min-bedrooms 2 --max-price 3000 --location cork --max-pages 5
  python daft_cli.py --help
        """
    )
    
    parser.add_argument(
        '--min-bedrooms',
        type=int,
        default=3,
        help='Минимальное количество спален (по умолчанию: 3)'
    )
    
    parser.add_argument(
        '--max-price',
        type=int,
        default=2500,
        help='Максимальная цена в евро (по умолчанию: 2500)'
    )
    
    parser.add_argument(
        '--location',
        type=str,
        default='dublin',
        help='Локация для поиска (по умолчанию: dublin)'
    )
    
    parser.add_argument(
        '--property-type',
        choices=['all', 'houses', 'apartments'],
        default='all',
        help='Тип недвижимости (по умолчанию: all)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=5,
        help='Максимальное количество страниц для обхода (по умолчанию: 5)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Уровень логирования (по умолчанию: INFO)'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['summary', 'detailed'],
        default='summary',
        help='Формат вывода результатов (по умолчанию: summary)'
    )
    
    return parser

async def main():
    """Основная функция CLI"""
    # Парсим аргументы
    parser = create_parser()
    args = parser.parse_args()
    
    print("🚀 DAFT.IE PARSER CLI")
    print("=" * 50)
    
    # Создаем парсер
    daft_parser = ProductionDaftParser(log_level=args.log_level)
    
    # Выводим параметры поиска
    print(f"🎯 ПАРАМЕТРЫ ПОИСКА:")
    print(f"   Минимум спален: {args.min_bedrooms}")
    print(f"   Максимальная цена: €{args.max_price}")
    print(f"   Локация: {args.location}")
    print(f"   Тип недвижимости: {args.property_type}")
    print(f"   Максимум страниц: {args.max_pages}")
    print(f"   Уровень логов: {args.log_level}")
    print()
    
    # Выполняем поиск
    try:
        results = await daft_parser.search_all_properties(
            min_bedrooms=args.min_bedrooms,
            max_price=args.max_price,
            location=args.location,
            property_type=args.property_type,
            max_pages=args.max_pages
        )
        
        # Выводим результаты
        print("\n" + "=" * 50)
        print("📋 РЕЗУЛЬТАТЫ")
        print("=" * 50)
        
        if args.output_format == 'summary':
            summary = daft_parser.format_results_summary(results)
            print(summary)
        else:
            # Детальный вывод
            for i, prop in enumerate(results, 1):
                print(f"\n{i}. {prop.get('title', 'Без названия')}")
                print(f"   💰 Цена: €{prop['price']}" if prop.get('price') else "   💰 Цена не указана")
                print(f"   🛏️  Спальни: {prop['bedrooms']}" if prop.get('bedrooms') else "   🛏️  Спальни не указаны")
                print(f"   🏠 Тип: {prop.get('property_type', 'Не указан')}")
                print(f"   📍 Локация: {prop.get('location', 'Не указана')}")
                if prop.get('description'):
                    print(f"   📝 Описание: {prop['description'][:100]}...")
                print(f"   🔗 URL: {prop['url']}")
        
        # Сохраняем результаты
        search_params = {
            'min_bedrooms': args.min_bedrooms,
            'max_price': args.max_price,
            'location': args.location,
            'property_type': args.property_type,
            'max_pages': args.max_pages
        }
        
        filename = daft_parser.save_results(results, search_params)
        print(f"\n💾 Подробные результаты сохранены в {filename}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Поиск прерван пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
