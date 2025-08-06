import requests
import json
from typing import List, Dict, Any, Optional

# --- CONFIGURATION ---
API_KEY = 'YOUR_API_KEY_HERE'
OHIO_COUNTY_FIPS_MAP = {
    'Franklin': '049', 'Cuyahoga': '035', 'Hamilton': '061',
    'Summit': '153', 'Montgomery': '113', 'Lucas': '095',
    'Stark': '151', 'Butler': '017', 'Lorain': '093',
    'Warren': '165', 'Delaware': '041', 'Greene': '057',
    'Clermont': '025', 'Clinton': '027', 'Preble': '135',

    'Clark': '023', 'Miami': '109', 'Darke': '037'
}
OHIO_STATE_FIPS = '39'


def get_municipal_demographics(county_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetches population and diversity data for all municipalities intersecting
    with a given list of Ohio counties.
    """
    if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
        raise ValueError("Census API Key is not set.")

    # Get the FIPS codes for the counties we want to filter by later.
    target_county_fips = {OHIO_COUNTY_FIPS_MAP[name] for name in county_names if name in OHIO_COUNTY_FIPS_MAP}

    CENSUS_VARS = {
        "P2_001N": "total_population", "P2_002N": "hispanic",
        "P2_005N": "white_non_hispanic", "P2_006N": "black_non_hispanic",
        "P2_007N": "native_non_hispanic", "P2_008N": "asian_non_hispanic",
        "P2_009N": "pacific_islander_non_hispanic", "P2_010N": "other_non_hispanic",
        "P2_011N": "multiracial_non_hispanic"
    }
    
    # We need the 'county' variable from the API to perform our filtering.
    get_vars_string = ",".join(["NAME", "county"] + list(CENSUS_VARS.keys()))
    
    all_municipalities_data = {}
    
    print("Fetching all demographic data for Ohio (this is more reliable)...")

    # --- THE FIX IS HERE ---
    # Instead of looping and querying per county, we make ONE call for the whole state.
    # This avoids the cross-county hierarchy error.
    # URL asks for all 'places' within the state of Ohio.
    url = (
        "https://api.census.gov/data/2020/dec/pl?"
        f"get={get_vars_string}&for=place:*&in=state:{OHIO_STATE_FIPS}&key={API_KEY}"
    )

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        headers = data[0]

        for row in data[1:]:
            row_data = dict(zip(headers, row))
            
            # --- AND THE FILTER IS HERE ---
            # Now, we check if the place's county is in our target list.
            if row_data['county'] not in target_county_fips:
                continue # Skip this place, it's not in a county we care about.

            total_pop = int(row_data.get("P2_001N", 0))
            if total_pop == 0:
                continue

            demographics = {"population": total_pop}
            
            for code, name in CENSUS_VARS.items():
                if "population" in name: continue
                count = int(row_data.get(code, 0))
                demographics[f"pct_{name}"] = round((count / total_pop) * 100, 2)
            
            clean_name = row_data["NAME"].replace(', Ohio', '')
            
            # This handles cases where a city (like Dublin) appears in multiple API rows
            # for its different county parts. We merge them or take the first entry.
            if clean_name not in all_municipalities_
                 all_municipalities_data[clean_name] = demographics

    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Could not fetch data for Ohio. {e}")
        print(f"  Response text: {response.text}") # Print the error response

    print("Data fetched and filtered successfully.")
    return all_municipalities_data

# The filter_and_sort function and the main execution block can remain the same.
def filter_and_sort_municipalities(
    demographics_ Dict[str, Dict[str, Any]],
    min_pop: int = 0,
    max_pop: Optional[int] = None
) -> List[Dict[str, Any]]:
    filtered_list = []
    for name, data in demographics_data.items():
        population = data.get("population", 0)
        if population >= min_pop and (max_pop is None or population <= max_pop):
            town_profile = {'name': name, **data}
            filtered_list.append(town_profile)
    sorted_list = sorted(filtered_list, key=lambda d: d['population'], reverse=True)
    return sorted_list

if __name__ == "__main__":
    counties_to_search = [
        'Montgomery',
        'Greene',
        'Warren',
        'Butler',
    ]
    MIN_POPULATION = 10000
    MAX_POPULATION = 100000
    
    all_demographic_data = get_municipal_demographics(counties_to_search)
    filtered_towns = filter_and_sort_municipalities(all_demographic_data, min_pop=MIN_POPULATION, max_pop=MAX_POPULATION)

    print("\n--- Final, Filtered Data Structure ---")
    print(json.dumps(filtered_towns, indent=2))
