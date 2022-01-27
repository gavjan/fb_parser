import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer

START_TIME = default_timer()


def fetch(session, job):
    with session.get(job['url']) as response:
        job['data'] = response.text
        if response.status_code != 200:
            print(f"FAILURE:{response.status_code}:{job['url']}")
        return job


async def get_data_asynchronous(jobs, callback):
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    executor,
                    fetch,
                    *(session, job)
                )
                for job in jobs
            ]
            for response in await asyncio.gather(*tasks):
                callback(response)


def async_get(jobs, callback):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(get_data_asynchronous(jobs, callback))
    loop.run_until_complete(future)


# Example
def main():
    jobs = [
        {'url': "https://topsale.am/product/calvin-klein-performance-heathered-logo-medium-impact-sports-bra/15900/",
         'arg': 1},
        {'url': "https://topsale.am/product/calvin-klein-performance-heathered-logo-medium-impact-sports-bra/15900/",
         'arg': 2},
        {'url': "https://topsale.am/product/calvin-klein-performance-heathered-logo-medium-impact-sports-bra/15900/",
         'arg': 3}
    ]

    def callback(job):
        print(f"{job['arg']}: {len(job['data'])}")

    async_get(jobs, callback, )


if __name__ == "__main__":
    main()
