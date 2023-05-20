import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures
from timeit import default_timer as timer
from datetime import timedelta
import sys

"""
todo:
•	Accept command line parameters for products to download
•	Accept command line parameters for folder to download pdf document to
"""


def load_url(download):

    pdf_download_url, file_path = download

#    print('-downloading {}'.format(pdf_download_url))

    # open in binary mode
    with open(file_path, "wb") as file:
        # get request
        response = requests.get(pdf_download_url)
        # write to file
        file.write(response.content)


def get_splunkdoc_products():
    print('Getting list of splunk products.')

    url = "https://docs.splunk.com/Documentation/Splunk"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    elements = soup.select('#product-select')
    pattern = 'value=\"([^\"]+)\">(.*)\</option>'

    elements_dict = {}

    for element in elements[0].contents:
        element = str(element)
        match = re.match(pattern, element, re.IGNORECASE)
        if match := re.search(pattern, element, re.IGNORECASE):
            key = match.group(1)

            value = match.group(2)
            value = value.replace('<sup>', '')
            value = value.replace('</sup>', '')

            elements_dict[key] = value

    return elements_dict


def get_splunkdoc_versions(product):
    url = "https://docs.splunk.com/Documentation/" + product
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    elements = soup.select('#version-select')
    pattern = 'value=\"([^\"]+)\">(.*)\</option>'

    elements_dict = {}

    for element in elements[0].contents:
        element = str(element)
        match = re.match(pattern, element, re.IGNORECASE)
        if match := re.search(pattern, element, re.IGNORECASE):
            key = match.group(1)

            value = match.group(2)
            value = value.replace('<sup>', '')
            value = value.replace('</sup>', '')

            elements_dict[key] = value

    return elements_dict


def main():
    start = timer()

    # create session object for re-use

    download_path = 'C:\Apps\splunkdocs'
    # my_products = get_splunkdoc_products()
    my_products = ['Splunk', 'Forwarder', 'DBX']
    my_products = ['Forwarder', 'DBX']
    my_products = ['Splunk', 'Forwarder', 'DSP', 'ES', 'SOARonprem', 'UBA', 'MC', 'SSE', 'ITSI', 'DBX']

    print('targeting products: {}'.format(', '.join([p for p in my_products])))

    download_list = []
    product_counter = 0
    for product in my_products:
        product_counter += 1
        print('working on product {} of {}: {}'.format(product_counter, len(my_products), product))

        versions = (get_splunkdoc_versions(product))

        for version in versions:
            if 'latest release' in versions[version]:

                print('-found latest release version: {}'.format(version))

                # get page for specified product and version as soup
                url = 'https://docs.splunk.com/Documentation/' + product + '/' + version
                page = requests.get(url)
                soup = BeautifulSoup(page.content, "html.parser")

                # process links listing documentation for product and version
                search_results = soup.find_all(href=re.compile('^/Documentation/' + product + '/' + version + '/'))

                search_result_counter = 0
                for i in search_results:

                    search_result_counter += 1

                    # get page associated with the document
                    page = requests.get('https://docs.splunk.com' + (i.attrs['href']))
                    soup = BeautifulSoup(page.content, "html.parser")

                    # get the links on document page associated pdfbook (effectively excluding topic)
                    for j in soup.find_all(href=re.compile('title=Documentation:.*&action=pdfbook&[^&]+&product=')):

                        # construct the download url
                        href = j.attrs['href']
                        pdf_download_url = 'https://docs.splunk.com' + href

                        # construct the download filename
                        document = (href.split(":"))[2]
                        file_name = product + '-' + version + '-' + document + '.pdf'
                        file_path = download_path + '\\' + file_name

                        download_list.append((pdf_download_url, file_path))
                        print('-adding document {} of {} with name {} as item {} in download list.'.format(search_result_counter, len(search_results), file_name, len(download_list)))

    # We can use a with statement to ensure threads are cleaned up promptly
    print('initializing up to {} concurrent downloads'.format('20'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(load_url, download_item): download_item for download_item in download_list}
        for future in concurrent.futures.as_completed(future_to_url):
            download_item = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (download_item, exc))
            else:
                pass

    end = timer()

    print('script execution completed with runtime: {}'.format(timedelta(seconds=end-start)))


if __name__=="__main__":
    main()
