from pprint import pprint
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pyprojroot import here
import requests
import requests_cache
from rich.console import Console
from rich.table import Table
from cachier import cachier
import datetime

requests_cache.install_cache(expire_after=60 * 60 * 2)

console = Console()


def get_url_list():
    URL = "https://www.wikidata.org/wiki/Special:EntityData/Q21980377.json"
    response = requests.get(URL)
    # TODO: handle 404
    urls_list = response.json()["entities"]["Q21980377"]["claims"]["P856"]
    clean_urls_list = list(
        map(lambda x: x["mainsnak"]["datavalue"]["value"], urls_list)
    )
    return clean_urls_list


@cachier(cache_dir=here(), stale_after=datetime.timedelta(hours=1))
def get_urls_report():
    report = []
    with requests_cache.disabled():
        for url in get_url_list():
            try:
                response = requests.get(url, timeout=1)
                report.append(
                    {
                        "URL": url,
                        "Status": response.status_code,
                        "Elapsed": response.elapsed.total_seconds(),
                    }
                )
            except requests.ConnectionError as e:
                report.append(
                    {
                        "URL": url,
                        "Status": e,
                        "Elapsed": None,
                    }
                )
    return report


def get_best_url():
    report = get_urls_report()
    best_url = sorted(
        list(filter(lambda r: r["Elapsed"], report)), key=lambda x: x["Elapsed"]
    )
    return list(best_url)[0]["URL"]


def render_report(report):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("URL", style="dim")
    table.add_column("Status")
    table.add_column("Elapsed")
    for r in report:
        str_args = [str(arg) for arg in r.values()]
        table.add_row(*str_args)
    return table


app = FastAPI()


@app.get("/go/{doi:path}")
async def go(doi: str = None):
    best_url = get_best_url()
    return RedirectResponse(f"{best_url}/{doi}")


# if __name__ == "__main__":
# report = get_urls_report()
# console.log(render_report(report))
# best_url = get_best_url()
# console.log(best_url)
