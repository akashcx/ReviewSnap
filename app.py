from flask import Flask, render_template, request
import pickle

import requests
from bs4 import BeautifulSoup
import openai
import os
from time import time, sleep
import textwrap
import re

def FinalFunction(inputURLbyUser):
    HEADERS = ({'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/90.0.4430.212 Safari/537.36',
                'Accept-Language': 'en-US, en;q=0.5'})

    def getdata(url):
        r = requests.get(url, headers=HEADERS)
        return r.text

    def html_code(url):
        htmldata = getdata(url)
        soup = BeautifulSoup(htmldata, 'html.parser')
        return (soup)

    input_url = inputURLbyUser
    temp1 = input_url.split("/", 6)

    soupProduct = html_code(input_url)
    product_input = ""
    for item in soupProduct.find_all("span", class_="a-size-large product-title-word-break"):
        product_input = product_input + item.get_text()
    product_input = product_input.strip()

    model_input_url = ""
    temp1[4] = "product-reviews"
    temp1[6] = "ref=cm_cr_arp_d_paging_btm_next_2?ie=UTF8&reviewerType=all_reviews&pageNumber="
    for i in range(0, 6):
        model_input_url += temp1[i]+"/"

    def cus_rev(soup):
        data_str = ""

        for item in soup.find_all("span", class_="a-size-base review-text review-text-content"):
            data_str = data_str + item.get_text()

        result = data_str.split("\n")

        rev_data = result
        rev_result = []
        for i in rev_data:
            if i == "":
                pass
            else:
                rev_result.append(i)
        return (rev_result)

    def findNumberOfReviewsPerStar(urlx, starx):
        urlx += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
            star=starx, page="1")
        soupx = html_code(urlx)
        nostr = ""
        for item in soupx.find_all("div", class_="a-row a-spacing-base a-size-base"):
            nostr = nostr+item.get_text()
        xn = nostr.split()[3]
        xnn = xn.split(",")
        numStarReview = ""
        for i in xnn:
            numStarReview += i
        return int(numStarReview)

    def extractReviewsIntoText(urlxy):
        oneStarReviews = [""]
        twoStarReviews = [""]
        threeStarReviews = [""]
        fourStarReviews = [""]
        fiveStarReviews = [""]
        if oneStarNumberPages < 3:
            for i in range(1, oneStarNumberPages+1):
                urlxyz = urlxy
                urlxyz += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
                    star="one", page=str(i))
                soupxy = html_code(urlxyz)
                rev2 = ""
                for j in cus_rev(soupxy):
                    oneStarReviews[0] += j
        else:
            for i in range(1, 4):
                urlxyz = urlxy
                urlxyz += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
                    star="one", page=str(i))
                soupxy = html_code(urlxyz)
                rev2 = ""
                for j in cus_rev(soupxy):
                    oneStarReviews[0] += j

        if twoStarNumberPages != 0:
            urlxyz = urlxy
            urlxyz += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
                star="two", page="1")
            soupxy = html_code(urlxyz)
            rev2 = ""
            for j in cus_rev(soupxy):
                twoStarReviews[0] += j

        if threeStarNumberPages != 0:
            urlxyz = urlxy
            urlxyz += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
                star="three", page="1")
            soupxy = html_code(urlxyz)
            rev2 = ""
            for j in cus_rev(soupxy):
                threeStarReviews[0] += j

        if fourStarNumberPages != 0:
            urlxyz = urlxy
            urlxyz += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
                star="four", page="1")
            soupxy = html_code(urlxyz)
            rev2 = ""
            for j in cus_rev(soupxy):
                fourStarReviews[0] += j

        if fiveStarNumberPages < 3:
            for i in range(1, fiveStarNumberPages+1):
                urlxyz = urlxy
                urlxyz += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
                    star="five", page=str(i))
                soupxy = html_code(urlxyz)
                rev2 = ""
                for j in cus_rev(soupxy):
                    fiveStarReviews[0] += j
        else:
            for i in range(1, 4):
                urlxyz = urlxy
                urlxyz += "ref=cm_cr_unknown?ie=UTF8&filterByStar={star}_star&reviewerType=all_reviews&pageNumber={page}#reviews-filter-bar".format(
                    star="five", page=str(i))
                soupxy = html_code(urlxyz)
                rev2 = ""
                for j in cus_rev(soupxy):
                    fiveStarReviews[0] += j
        return [oneStarReviews, twoStarReviews, threeStarReviews, fourStarReviews, fiveStarReviews]

    def open_file(filepath):
        with open(filepath, 'r', encoding='utf-8') as infile:
            return infile.read()

    openai.api_key = os.getenv("api_key")

    def save_file(content, filepath):
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

    def gpt3_completion(prompt, engine='text-davinci-003', temp=0.7, top_p=1.0, tokens=1000, freq_pen=0.5, pres_pen=0.5, stop=['<<END>>']):
        max_retry = 5
        retry = 0
        while True:
            try:
                response = openai.Completion.create(
                    engine=engine,
                    prompt=prompt,
                    temperature=temp,
                    max_tokens=tokens,
                    top_p=top_p,
                    frequency_penalty=freq_pen,
                    presence_penalty=pres_pen,
                    stop=stop)
                text = response['choices'][0]['text'].strip()
                text = re.sub('\s+', ' ', text)
                return text
            except Exception as oops:
                retry += 1
                if retry >= max_retry:
                    return "GPT3 error: %s" % oops
                print('Error communicating with OpenAI:', oops)
                sleep(1)

    def beautifySummary(summary):
        a1 = summary.split("Strengths: ")
        strengths = "Strengths: " + a1[1].split("Weaknesses: ")[0]
        weaknesses = "Weaknesses: " + \
            a1[1].split("Weaknesses: ")[1].split("Functionality: ")[0]
        functionality = "Functionality: " + \
            a1[1].split("Weaknesses: ")[1].split(
                "Functionality: ")[1].split("Worthiness: ")[0]
        worthiness = "Worthiness: " + \
            a1[1].split("Weaknesses: ")[1].split(
                "Functionality: ")[1].split("Worthiness: ")[1]
        return (product_input, strengths, weaknesses, functionality, worthiness)

    oneStarNumberPages = findNumberOfReviewsPerStar(model_input_url, "one")//10
    twoStarNumberPages = findNumberOfReviewsPerStar(model_input_url, "two")//10
    threeStarNumberPages = findNumberOfReviewsPerStar(
        model_input_url, "three")//10
    fourStarNumberPages = findNumberOfReviewsPerStar(
        model_input_url, "four")//10
    fiveStarNumberPages = findNumberOfReviewsPerStar(
        model_input_url, "five")//10

    a = extractReviewsIntoText(model_input_url)
    alltext = ""
    for i in a:
        alltext += i[0]
    chunks = textwrap.wrap(alltext, 4000)
    result = list()
    promptText1 = """ Produce a summary of the following reviews. Classify your summary into strengths, weaknesses, functionality and worthiness without redundancy:
<<SUMMARY>>
SUMMARY HIGHLIGHTING KEY STRENGTHS, WEAKNESSES, FUNCTIONALITY, WORTHINESS: """

    count = 0
    for chunk in chunks:
        count = count + 1
        prompt = promptText1.replace('<<SUMMARY>>', chunk)
        summary = gpt3_completion(prompt)
        result.append(summary)

    result = '\n\n'.join(result)

    promptText2 = """ Classify your summary into strengths, weaknesses, functionality and worthiness with NO repitition or redundancy:
<<SUMMARY>>
NON-REDUNDANT AND NON-CONFLICTING SUMMARY HIGHLIGHTING KEY STRENGTHS, WEAKNESSES, FUNCTIONALITY, WORTHINESS: """

    if (len(result)*0.25) < 3000:
        summaryFinal = gpt3_completion(
            promptText2.replace('<<SUMMARY>>', result))
        summaryFinal = beautifySummary(summaryFinal)
        return summaryFinal
    else:
        result_chunks = textwrap.wrap(result, 4000)
        result2 = list()
        for result_chunk in result_chunks:
            result_chunk_summary = gpt3_completion(
                promptText2.replace('<<SUMMARY>>', result_chunk))
            result2.append(result_chunk_summary)
        result2 = '\n\n'.join(result2)
        summaryFinal = gpt3_completion(
            promptText2.replace('<<SUMMARY>>', result2))
        print()
        summaryFinal = beautifySummary(summaryFinal)
        return summaryFinal

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    link = request.form['link']
    a, b, c, d, e = FinalFunction(link)
    return render_template('predict.html', a=a, b=b, c=c, d=d, e=e)

if __name__ == '__main__':
    app.run()
