# A normal desktop Chrome string. Headless Chromium announces itself as
# "HeadlessChrome" by default, which some job boards block on sight.
SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
)

VALID_MARKETS = {
    "canada",
    "usa",
    "north-america",
}

VALID_EXPERIENCE_LEVELS = {
    "all",
    "junior",
    "senior",
}

# ============================================================
# BUILT IN
# ============================================================

BUILT_IN_URLS = {
    "canada": {
        "all": "/jobs/remote/hybrid/office/engineering?country=CAN&allLocations=true",
        "junior": "/jobs/remote/hybrid/office/engineering/entry-level/junior?country=CAN&allLocations=true",
        "senior": "/jobs/remote/hybrid/office/engineering/mid-level/senior/expert-leader?country=CAN&allLocations=true",
    },

    "usa": {
        "all": "/jobs/remote/hybrid/office/engineering?city=&state=&country=USA&allLocations=true",
        "junior": "/jobs/remote/hybrid/office/engineering/entry-level/junior?country=USA&allLocations=true",
        "senior": "/jobs/remote/hybrid/office/engineering/mid-level/senior/expert-leader?country=USA&allLocations=true",
    },
}


# ============================================================
# WELLFOUND
# ============================================================

# Role pages list every level together, and each position states the
# years of experience it requires, so junior vs senior is decided by
# the analyzer rather than by separate URLs. Pages are paginated with
# ?page=N.
#
# Note: "/role/l/engineer/usa-startups" silently redirects to the
# worldwide /role/engineer page -- use "united-states" for the US.
WELLFOUND_URLS = {
    "canada": [
        "/role/l/engineer/canada-startups",
        "/role/l/developer/canada-startups",
    ],

    "usa": [
        "/role/l/engineer/united-states",
        "/role/l/developer/united-states",
    ],
}

# Listing pages to read per URL. Public role pages run out after about
# 8 pages (~230 positions across both role URLs); the scraper also stops
# early when a page has no "Next" link, so this is a ceiling.
WELLFOUND_PAGES_PER_URL = 10

# ============================================================
# JOB BANK
# ============================================================

JOB_BANK_URLS = {
    "canada": {
        "all": "https://www.jobbank.gc.ca/jobsearch/jobsearch?fcid=5169&fcid=12083&fcid=17880&fcid=24510&fcid=25803&fcid=296553&fcid=296554&fcid=296805&fn21=21230&fn21=21231&fn21=21232&fn21=21234&fn21=94153&page=1&sort=D&term=data+engineer&term=developer&term=engineer&term=software+engineer%2C+software",
        "junior": "...",
        "senior": "https://www.jobbank.gc.ca/jobsearch/jobsearch?fcid=227158&fcid=298109&term=senior+software+developer&term=senior+software+engineer&page=1&sort=D",
    },
}

# all : https://simplify.jobs/jobs?q=software+engineer&type=Full-Time&type=Part-Time&type=Contract&functions=QA+%26+Testing&functions=Software+Engineering&functions=DevOps+%26+Infrastructure&functions=Implementation+%26+Technical+Account+Management&functions=Full-Stack+Engineering&functions=Backend+Engineering&functions=AI+Application+Engineering&functions=Test+Automation+Engineering&functions=Frontend+Engineering&functions=Applied+Machine+Learning&functions=Solution+Engineering&functions=DevOps+Engineering&functions=Cloud+Engineering&functions=Data+Engineering&functions=AI+%26+Machine+Learning&functions=Mobile+Engineering&functions=Embedded+Engineering&functions=Systems+Software+Engineering&functions=Data+%26+Analytics&location=bbox%7E43.921675%2C-79.703046%2C43.56782%2C-79.173476%7EToronto&location=bbox%7E49.352454%2C-123.258758%2C49.198445%2C-123.014741%7EVancouver&location=bbox%7E51.2125013%2C-114.3157587%2C50.842526%2C-113.8600018%7ECalgary&location=bbox%7E53.7162646%2C-113.7138411%2C53.3372558%2C-113.2714783%7EEdmonton&location=bbox%7E45.7047897%2C-73.9741567%2C45.4100756%2C-73.4742952%7EMontreal&location=bbox%7E45.5376502%2C-76.3555857%2C44.9617738%2C-75.2465783%7EOttawa&location=bbox%7E49.9940075%2C-97.3491505%2C49.7135538%2C-96.9565293%7EWinnipeg&location=bbox%7E46.9806797%2C-71.5492175%2C46.7277099%2C-71.1336606%7EQuebec+City&sort=recent&job=e2230fbe-8777-4bdd-a0a1-b2c6e6f893e2
# junior: https://simplify.jobs/jobs?q=software+engineer&type=Full-Time&type=Part-Time&type=Contract&experience_level=Entry+Level%2FNew+Grad&experience_level=Junior&functions=QA+%26+Testing&functions=Software+Engineering&functions=DevOps+%26+Infrastructure&functions=Implementation+%26+Technical+Account+Management&functions=Full-Stack+Engineering&functions=Backend+Engineering&functions=AI+Application+Engineering&functions=Test+Automation+Engineering&functions=Frontend+Engineering&functions=Applied+Machine+Learning&functions=Solution+Engineering&functions=DevOps+Engineering&functions=Cloud+Engineering&functions=Data+Engineering&functions=AI+%26+Machine+Learning&functions=Mobile+Engineering&functions=Embedded+Engineering&functions=Systems+Software+Engineering&functions=Data+%26+Analytics&location=bbox%7E43.921675%2C-79.703046%2C43.56782%2C-79.173476%7EToronto&location=bbox%7E49.352454%2C-123.258758%2C49.198445%2C-123.014741%7EVancouver&location=bbox%7E51.2125013%2C-114.3157587%2C50.842526%2C-113.8600018%7ECalgary&location=bbox%7E53.7162646%2C-113.7138411%2C53.3372558%2C-113.2714783%7EEdmonton&location=bbox%7E45.7047897%2C-73.9741567%2C45.4100756%2C-73.4742952%7EMontreal&location=bbox%7E45.5376502%2C-76.3555857%2C44.9617738%2C-75.2465783%7EOttawa&location=bbox%7E49.9940075%2C-97.3491505%2C49.7135538%2C-96.9565293%7EWinnipeg&location=bbox%7E46.9806797%2C-71.5492175%2C46.7277099%2C-71.1336606%7EQuebec+City&sort=recent&job=e2230fbe-8777-4bdd-a0a1-b2c6e6f893e2
# senior: https://simplify.jobs/jobs?q=software+engineer&type=Full-Time&type=Part-Time&type=Contract&experience_level=Mid+Level&experience_level=Senior&experience_level=Expert+or+higher&functions=QA+%26+Testing&functions=Software+Engineering&functions=DevOps+%26+Infrastructure&functions=Implementation+%26+Technical+Account+Management&functions=Full-Stack+Engineering&functions=Backend+Engineering&functions=AI+Application+Engineering&functions=Test+Automation+Engineering&functions=Frontend+Engineering&functions=Applied+Machine+Learning&functions=Solution+Engineering&functions=DevOps+Engineering&functions=Cloud+Engineering&functions=Data+Engineering&functions=AI+%26+Machine+Learning&functions=Mobile+Engineering&functions=Embedded+Engineering&functions=Systems+Software+Engineering&functions=Data+%26+Analytics&location=bbox%7E43.921675%2C-79.703046%2C43.56782%2C-79.173476%7EToronto&location=bbox%7E49.352454%2C-123.258758%2C49.198445%2C-123.014741%7EVancouver&location=bbox%7E51.2125013%2C-114.3157587%2C50.842526%2C-113.8600018%7ECalgary&location=bbox%7E53.7162646%2C-113.7138411%2C53.3372558%2C-113.2714783%7EEdmonton&location=bbox%7E45.7047897%2C-73.9741567%2C45.4100756%2C-73.4742952%7EMontreal&location=bbox%7E45.5376502%2C-76.3555857%2C44.9617738%2C-75.2465783%7EOttawa&location=bbox%7E49.9940075%2C-97.3491505%2C49.7135538%2C-96.9565293%7EWinnipeg&location=bbox%7E46.9806797%2C-71.5492175%2C46.7277099%2C-71.1336606%7EQuebec+City&sort=recent&job=e2230fbe-8777-4bdd-a0a1-b2c6e6f893e2

SIMPLIFYJOBS_API_URL = (
    "https://js-ha.simplify.jobs/multi_search"
    "?use_cache=true&cache_ttl=120"
)

SIMPLIFYJOBS_QUERY = "software engineer"
SIMPLIFYJOBS_PER_PAGE = 21
SIMPLIFYJOBS_MAX_PAGES = 10

# SimplifyJobs currently has Canadian location filters configured.
SIMPLIFYJOBS_EXPERIENCE_FILTERS = {
    "all": None,
    "junior": (
        "experience_level:=[`Entry Level/New Grad`, `Junior`]"
    ),
    "senior": (
        "experience_level:=[`Mid Level`, `Senior`, "
        "`Expert or higher`]"
    ),
}

SIMPLIFYJOBS_JOB_TYPES_FILTER = (
    "type:=[`Full-Time`, `Part-Time`, `Contract`]"
)

SIMPLIFYJOBS_FUNCTIONS_FILTER = (
    "functions:=["
    "`QA & Testing`, "
    "`Software Engineering`, "
    "`DevOps & Infrastructure`, "
    "`Implementation & Technical Account Management`, "
    "`Full-Stack Engineering`, "
    "`Backend Engineering`, "
    "`AI Application Engineering`, "
    "`Test Automation Engineering`, "
    "`Frontend Engineering`, "
    "`Applied Machine Learning`, "
    "`Solution Engineering`, "
    "`DevOps Engineering`, "
    "`Cloud Engineering`, "
    "`Data Engineering`, "
    "`AI & Machine Learning`, "
    "`Mobile Engineering`, "
    "`Embedded Engineering`, "
    "`Systems Software Engineering`, "
    "`Data & Analytics`"
    "]"
)

SIMPLIFYJOBS_CANADA_LOCATIONS_FILTER = (
    "(geolocations:(43.921675, -79.703046, "
    "43.921675, -79.173476, 43.56782, -79.173476, "
    "43.56782, -79.703046) || "
    "geolocations:(49.352454, -123.258758, "
    "49.352454, -123.014741, 49.198445, -123.014741, "
    "49.198445, -123.258758) || "
    "geolocations:(51.2125013, -114.3157587, "
    "51.2125013, -113.8600018, 50.842526, -113.8600018, "
    "50.842526, -114.3157587) || "
    "geolocations:(53.7162646, -113.7138411, "
    "53.7162646, -113.2714783, 53.3372558, -113.2714783, "
    "53.3372558, -113.7138411) || "
    "geolocations:(45.7047897, -73.9741567, "
    "45.7047897, -73.4742952, 45.4100756, -73.4742952, "
    "45.4100756, -73.9741567) || "
    "geolocations:(45.5376502, -76.3555857, "
    "45.5376502, -75.2465783, 44.9617738, -75.2465783, "
    "44.9617738, -76.3555857) || "
    "geolocations:(49.9940075, -97.3491505, "
    "49.9940075, -96.9565293, 49.7135538, -96.9565293, "
    "49.7135538, -97.3491505) || "
    "geolocations:(46.9806797, -71.5492175, "
    "46.9806797, -71.1336606, 46.7277099, -71.1336606, "
    "46.7277099, -71.5492175))"
)


def build_simplifyjobs_filter(experience: str = "all") -> str:
    if experience not in SIMPLIFYJOBS_EXPERIENCE_FILTERS:
        raise ValueError(
            f"Unsupported SimplifyJobs experience level: {experience}"
        )

    filters = [
        SIMPLIFYJOBS_JOB_TYPES_FILTER,
        SIMPLIFYJOBS_FUNCTIONS_FILTER,
        SIMPLIFYJOBS_CANADA_LOCATIONS_FILTER,
    ]

    experience_filter = SIMPLIFYJOBS_EXPERIENCE_FILTERS[experience]

    if experience_filter:
        filters.append(experience_filter)

    return " && ".join(filters)
