import base64
from collections import Counter
import os
import time
import io

from django.shortcuts import render
from django.views.generic import TemplateView
from discogs_stat_basic.forms import NicknameRequestForm


import requests
import matplotlib.pyplot as plt
import seaborn


AUTHORIZATION_TOKEN = f"Discogs token={os.getenv('DISCOGS_TOKEN')}"
BASE_API_URL = "https://api.discogs.com"
USER_AGENT = "FooBarApp/3.0"
default_request_headers = {
    "User-Agent": USER_AGENT,
    "Authorization": AUTHORIZATION_TOKEN,
}
# Create your views here.


class MainFormView(TemplateView):
    template_name = "index.html"
    form_class = NicknameRequestForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            genre_percentages = []
            default_collection_genres = []
            data = form.cleaned_data
            default_user_collection = requests.get(
                BASE_API_URL + f"/users/{data['discogs_nickname']}/collection/folders/0/releases",
                params={"per_page": 500, "page": 1}
            )
            collection_items_total = default_user_collection.json()["pagination"]["items"]
            total_pages = default_user_collection.json()["pagination"]["pages"]
            for page in range(1, total_pages + 1):
                default_user_collection_page = requests.get(
                    BASE_API_URL + f"/users/{data['discogs_nickname']}/collection/folders/0/releases",
                    params={"per_page": 500, "page": page}
                )
                if (total_pages > 5) and (page >= total_pages // 2):
                    time.sleep(3)
                try:
                    for release in default_user_collection_page.json()["releases"]:
                        default_collection_genres.extend(release["basic_information"]["genres"])
                except KeyError:
                    print(default_user_collection_page.json())
        for genre, count in Counter(default_collection_genres).items():
            percentage = (count / collection_items_total) * 100
            genre_percentages.append({"genre": genre, "percentage": percentage})

        img_buffer = self.generate_genre_plot(genre_percentages)
        img_data = img_buffer.getvalue()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        return render(
            request, 
            self.template_name, 
            {
                "form": form, 
                "genre_percentages": genre_percentages,
                "plot_image": img_base64
            }
        )
    

    def generate_genre_plot(self, genre_percentages):
        """Generate a matplotlib plot of genre percentages and return it as a bytes buffer."""
        genres = [item['genre'] for item in genre_percentages]
        percentages = [item['percentage'] for item in genre_percentages]
        plt.figure(figsize=(16, 8))
        seaborn.barplot(x=genres, y=percentages, palette="pastel", orient="v")
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        plt.close()
        
        return buffer
