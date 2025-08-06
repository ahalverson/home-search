import requests
import json
from typing import List, Dict, Any, Optional

# --- CONFIGURATION ---
# 1. PASTE YOUR CENSUS API KEY HERE
API_KEY = 'YOUR_API_KEY_HERE'

# FIPS codes for Ohio counties
OHIO_COUNTY_FIPS_MAP = {
    'Franklin': '049', 'Cuyahoga': '035', 'Hamilton': '061',
    'Summit': '153', 'Montgomery': '113', 'Lucas': '095',
    'Stark': '151', 'Butler': '017', 'Lorain': '093',
    'Warren': '165', 'Delaware': '041', 'Greene': '057',
    'Clermont': '025',
}
OHIO_STATE_FIPS = '39'


def get_municipal_demographics(county_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetches population and diversity data for all municipalities in a list of counties.

    Args:
        county_names: A list of county names to search within.

    Returns:
        A nested dictionary mapping municipality names to their demographic data, e.g.,
        {'Dublin city': {'population': 49328, 'pct_white': 68.4, ...}}
    """
    if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
        raise ValueError("Census API Key is not set. Please add it to the script.")

    # Census variable codes from the 2020 Decennial Census (Table P2)
    # See all variables: https://api.census.gov/data/2020/dec/pl/variables.html
    CENSUS_VARS = {
        "P2_001N": "total_population",
        "P2_002N": "hispanic",
        "P2_005N": "white_non_hispanic",
        "P2_006N": "black_non_hispanic",
        "P2_007N": "native_non_hispanic",
        "P2_008N": "asian_non_hispanic",
        "P2_009N": "pacific_islander_non_hispanic",
        "P2_010N": "other_non_hispanic",
        "P2_011N": "multiracial_non_hispanic",
    }
    
    get_vars_string = ",".join(["NAME"] + list(CENSUS_VARS.keys()))
    all_municipalities_data = {}
    
    print("Fetching demographic data from the U.S. Census Bureau...")

    for county_name in county_names:
        county_fips = OHIO_COUNTY_FIPS_MAP.get(county_name)
        if not county_fips:
            print(f"Warning: County '{county_name}' not found. Skipping.")
            continue

        print(f"-> Searching in {county_name} County...")
        url = (
            "https://api.census.gov/data/2020/dec/pl?"
            f"get={get_vars_string}&for=place:*&in=state:{OHIO_STATE_FIPS}+county:{county_fips}&key={API_KEY}"
        )
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            headers = data[0]
            
            for row in data[1:]:
                row_data = dict(zip(headers, row))
                
                total_pop = int(row_data.get("P2_001N", 0))
                if total_pop == 0:
                    continue # Skip places with no population

                demographics = {"population": total_pop}
                
                # Calculate percentages for each group
                for code, name in CENSUS_VARS.items():
                    if "population" in name: continue # Skip total count
                    count = int(row_data.get(code, 0))
                    demographics[f"pct_{name}"] = round((count / total_pop) * 100, 2)
                
                clean_name = row_data["NAME"].replace(', Ohio', '')
                all_municipalities_data[clean_name] = demographics

        except requests.exceptions.RequestException as e:
            print(f"  ERROR: Could not fetch data for {county_name} County. {e}")

    return all_municipalities_data


def filter_and_sort_municipalities(
    demographics_ Dict[str, Dict[str, Any]],
    min_pop: int = 0,
    max_pop: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filters and sorts municipality data, returning it as a list of dictionaries.

    Args:
        demographics_ The raw dictionary from get_municipal_demographics.
        min_pop: The minimum population to include.
        max_pop: The maximum population to include. Use None for no upper limit.

    Returns:
        A sorted list of dictionaries, with each dictionary representing a town
        and its full demographic profile.
    """
    filtered_list = []
    for name, data in demographics_data.items():
        population = data.get("population", 0)
        if population >= min_pop and (max_pop is None or population <= max_pop):
            # Create a new, flat dictionary with the name included
            town_profile = {'name': name, **data}
            filtered_list.append(town_profile)
    
    # Sort the final list by population in descending order
    sorted_list = sorted(filtered_list, key=lambda d: d['population'], reverse=True)
    
    return sorted_list


if __name__ == "__main__":
    # --- STEP 1: Define your search criteria ---
    counties_to_search = [
        'Franklin',
        'Delaware',
    ]
    MIN_POPULATION = 30000
    MAX_POPULATION = 100000

    # --- STEP 2: Fetch all data from the API ---
    all_demographic_data = get_municipal_demographics(counties_to_search)

    # --- STEP 3: Filter and sort the data to get your target list ---
    filtered_towns = filter_and_sort_municipalities(
        all_demographic_data,
        min_pop=MIN_POPULATION,
        max_pop=MAX_POPULATION
    )

    # --- STEP 4: Use the final data in your project ---
    # `filtered_towns` now holds the clean, detailed data you need.

    # For demonstration, we'll print the final list of dictionaries in a readable format.
    print("\n--- Final, Filtered Data Structure ---")
    print(json.dumps(filtered_towns, indent=2))
    
    print(f"\nFound {len(filtered_towns)} municipalities matching the criteria.")
