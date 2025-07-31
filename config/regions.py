#!/usr/bin/env python3
"""
Конфигурация регионов и параметров поиска для Daft.ie
"""

# Список всех доступных регионов в Дублине с их URL-идентификаторами
DUBLIN_REGIONS = {
    "dublin-city": "Dublin City Centre",
    "dublin-1": "Dublin 1",
    "dublin-2": "Dublin 2", 
    "dublin-3": "Dublin 3",
    "dublin-4": "Dublin 4",
    "dublin-5": "Dublin 5",
    "dublin-6": "Dublin 6",
    "dublin-6w": "Dublin 6W",
    "dublin-7": "Dublin 7",
    "dublin-8": "Dublin 8",
    "dublin-9": "Dublin 9",
    "dublin-10": "Dublin 10",
    "dublin-11": "Dublin 11",
    "dublin-12": "Dublin 12",
    "dublin-13": "Dublin 13",
    "dublin-14": "Dublin 14",
    "dublin-15": "Dublin 15",
    "dublin-16": "Dublin 16",
    "dublin-17": "Dublin 17",
    "dublin-18": "Dublin 18",
    "dublin-20": "Dublin 20",
    "dublin-22": "Dublin 22",
    "dublin-24": "Dublin 24",
    
    # Популярные районы Дублина
    "ballymun": "Ballymun",
    "blackrock": "Blackrock",
    "blanchardstown": "Blanchardstown",
    "booterstown": "Booterstown",
    "cabra": "Cabra",
    "castleknock": "Castleknock",
    "clondalkin": "Clondalkin",
    "clonskeagh": "Clonskeagh",
    "clontarf": "Clontarf",
    "crumlin": "Crumlin",
    "dalkey": "Dalkey",
    "deansgrange": "Deansgrange",
    "donnybrook": "Donnybrook",
    "drumcondra": "Drumcondra",
    "dundrum": "Dundrum",
    "dun-laoghaire": "Dún Laoghaire",
    "finglas": "Finglas",
    "foxrock": "Foxrock",
    "glasnevin": "Glasnevin",
    "howth": "Howth",
    "kilmainham": "Kilmainham",
    "lucan": "Lucan",
    "malahide": "Malahide",
    "milltown": "Milltown",
    "mount-merrion": "Mount Merrion",
    "phibsborough": "Phibsborough",
    "portmarnock": "Portmarnock",
    "raheny": "Raheny",
    "ranelagh": "Ranelagh",
    "rathfarnham": "Rathfarnham",
    "rathgar": "Rathgar",
    "rathmines": "Rathmines",
    "ringsend": "Ringsend",
    "sandymount": "Sandymount",
    "stillorgan": "Stillorgan",
    "sutton": "Sutton",
    "tallaght": "Tallaght",
    "terenure": "Terenure",
    "walkinstown": "Walkinstown"
}

# Основные города Ирландии (по данным с Daft.ie)
MAIN_CITIES = {
    # Explore by City секция
    "dublin": "Dublin",
    "cork": "Cork",
    "galway": "Galway",
    "belfast": "Belfast",
    "limerick": "Limerick",
    "waterford": "Waterford"
}

# Все графства Ирландии и Северной Ирландии (по данным с Daft.ie)
COUNTIES = {
    # Северная Ирландия
    "antrim": "Co. Antrim",
    "armagh": "Co. Armagh",
    "derry": "Co. Derry",
    "down": "Co. Down",
    "fermanagh": "Co. Fermanagh",
    "tyrone": "Co. Tyrone",
    
    # Республика Ирландия
    "carlow": "Co. Carlow",
    "cavan": "Co. Cavan",
    "clare": "Co. Clare",
    "cork-county": "Co. Cork",
    "donegal": "Co. Donegal",
    "dublin-county": "Co. Dublin",
    "galway-county": "Co. Galway",
    "kerry": "Co. Kerry",
    "kildare": "Co. Kildare",
    "kilkenny": "Co. Kilkenny",
    "laois": "Co. Laois",
    "leitrim": "Co. Leitrim",
    "limerick-county": "Co. Limerick",
    "longford": "Co. Longford",
    "louth": "Co. Louth",
    "mayo": "Co. Mayo",
    "meath": "Co. Meath",
    "monaghan": "Co. Monaghan",
    "offaly": "Co. Offaly",
    "roscommon": "Co. Roscommon",
    "sligo": "Co. Sligo",
    "tipperary": "Co. Tipperary",
    "waterford-county": "Co. Waterford",
    "westmeath": "Co. Westmeath",
    "wexford": "Co. Wexford",
    "wicklow": "Co. Wicklow"
}

# Объединенный список всех доступных локаций для поиска
ALL_LOCATIONS = {**DUBLIN_REGIONS, **MAIN_CITIES, **COUNTIES}

# Настройки по умолчанию (обновлено по данным Daft.ie)
DEFAULT_SETTINGS = {
    "regions": ["dublin-city"],  # Может быть район, город или графство
    "min_bedrooms": 3,
    "max_price": 2500,
    "monitoring_interval": 3600,  # 1 час в секундах
    "max_results_per_search": 50
}

# Лимиты для валидации (расширены для поддержки всей Ирландии)
LIMITS = {
    "min_bedrooms": {"min": 0, "max": 10},
    "max_price": {"min": 500, "max": 15000},  # Увеличен лимит для Дублина
    "monitoring_interval": {"min": 300, "max": 86400},  # от 5 минут до 24 часов
    "max_regions": 15,  # Увеличено для поддержки нескольких графств
    "max_results_per_search": {"min": 10, "max": 100}
}

# Популярные комбинации для быстрого доступа
POPULAR_COMBINATIONS = {
    "dublin_central": ["dublin-city", "dublin-2", "dublin-4"],
    "dublin_south": ["dublin-6", "rathmines", "ranelagh", "donnybrook"],
    "dublin_north": ["dublin-1", "dublin-3", "dublin-5", "clontarf"],
    "dublin_west": ["dublin-7", "dublin-8", "clondalkin", "lucan"],
    "major_cities": ["dublin", "cork", "galway", "limerick"],
    "student_areas": ["dublin-city", "rathmines", "drumcondra", "glasnevin"]
}

# Категории регионов для удобной навигации
REGION_CATEGORIES = {
    "dublin_areas": DUBLIN_REGIONS,
    "main_cities": MAIN_CITIES, 
    "counties": COUNTIES,
    "northern_ireland": {k: v for k, v in COUNTIES.items() 
                        if k in ["antrim", "armagh", "derry", "down", "fermanagh", "tyrone"]},
    "republic_of_ireland": {k: v for k, v in COUNTIES.items() 
                           if k not in ["antrim", "armagh", "derry", "down", "fermanagh", "tyrone"]}
}
