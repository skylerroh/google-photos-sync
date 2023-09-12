import datetime
from datetime import timedelta
import requests
import os
import datetime
from p_tqdm import p_map, p_umap, p_imap, p_uimap
from events import EventList

class SharedAlbum:
    def __init__(
            self,
            id,
            service,
            title,
            productUrl,
            mediaItemsCount=None,
            coverPhotoBaseUrl=None,
            coverPhotoMediaItemId=None,
            **kwargs
    ):
        self.id = id
        self.title = title
        self.product_url = productUrl
        self.service = service
        self.media_items_count = mediaItemsCount
        self.event_list = None

    def get_date(self, media_item):
        creation_time = datetime.datetime.fromisoformat(media_item['mediaMetadata']['creationTime'][:-1])
        return creation_time

    @staticmethod
    def create_dir_if_not_exists(dir_path):
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        return dir_path

    def create_local_subfolder(self, top_folder):
        sub_folder = os.path.join(top_folder.rstrip("/"), self.title)
        return self.create_dir_if_not_exists(sub_folder)

    def download_and_rename(self, destination_folder, start_date=None, end_date=None, dry_run=False):
        sub_folder = self.create_local_subfolder(destination_folder)
        media_items = self.list_media(start_date=start_date, end_date=end_date)
        media_items = sorted(media_items, key=self.get_date)
        print(f"number of items to download: {len(media_items)}")

        if dry_run:
            print(media_items)
        else:
            p_map(lambda x: self.download(x, sub_folder), media_items)

    def create_date_filter(cls, start_date, end_date=None):
        if not end_date:
            end_date = datetime.datetime.today() + timedelta(days=1)
        return {
            "dateFilter": {
                "ranges": [
                    {
                        "startDate": {
                            "year": start_date.year,
                            "month": start_date.month,
                            "day": start_date.day
                        },
                        "endDate": {
                            "year": end_date.year,
                            "month": end_date.month,
                            "day": end_date.day
                        }
                    }
                ]
            }
        }

    def list_media(self, start_date = None, end_date = None, page_number=1, nextPageToken=None, limit=None):
        page_size = 100
        body = {"pageSize": page_size, "albumId": self.id}
        if nextPageToken:
            body["pageToken"] = nextPageToken
        response = self.service.mediaItems().search(body=body).execute()
        print(f"received media {(page_number) * page_size} / {self.media_items_count}")
        media_items = response["mediaItems"]

        if start_date:
            if not end_date:
                end_date = datetime.datetime.today() + timedelta(days=1)
            media_items = [mi
                          for mi
                          in media_items
                          if self.get_date(mi) >= start_date and self.get_date(mi) <= end_date]

        nextPageToken = response.get("nextPageToken")
        if limit is not None and (page_size * page_number) > limit:
            return media_items[:limit - (page_size * (page_number - 1))]
        else:
            return media_items + (self.list_media(page_number=page_number + 1, nextPageToken=nextPageToken,
                                                  limit=limit) if nextPageToken else [])

    def download(self, item, destination_folder):
        url = item['baseUrl']
        if 'video' in item['mimeType']:
            url += '=dv'
            status = item["mediaMetadata"]["video"]["status"]
            if status != "READY":
                print(f"{status}: {item['id']}")
        elif 'image' in item['mimeType']:
            url += '=d'

        response = requests.get(url)

        creation_time = self.get_date(item)
        date_str = creation_time.strftime('%Y%m%d')
        yearmonth_str = creation_time.strftime('%Y%m')
        yearmonth_folder = self.create_dir_if_not_exists(os.path.join(destination_folder, yearmonth_str))
        event_collection = self.event_list.find_event(creation_time.date())

        file_name = f"""{date_str}_{self.title}_{item['id']}_{item['filename']}"""
        if event_collection:
            event_path = os.path.join(destination_folder, "events")
            self.create_dir_if_not_exists(event_path)
            event_start_and_name = f"""{event_collection.start_date.strftime("%Y%m%d")}_{event_collection.name.replace(" ", "_")}"""
            event_folder = self.create_dir_if_not_exists(os.path.join(event_path, event_start_and_name))
            file_name = file_name.replace(date_str, event_start_and_name)
            with open(os.path.join(event_folder, file_name), 'wb') as f:
                f.write(response.content)
                f.close()

        with open(os.path.join(yearmonth_folder, file_name), 'wb') as f:
            f.write(response.content)
            f.close()
