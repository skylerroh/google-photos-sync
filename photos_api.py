from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import argparse
import datetime
import pickle
from config import Config
from shared_album import SharedAlbum

class PhotosApi:
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly',
              'https://www.googleapis.com/auth/photoslibrary.sharing']

    def __init__(self):
        self.service = self.get_service(self.SCOPES)

    def get_service(self, scopes, creds=None):
        if not creds or not creds.valid:
            if (creds and creds.expired and creds.refresh_token):
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(Config.client_secrets_file, scopes)
                creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as tokenFile:
                pickle.dump(creds, tokenFile)
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        return service

    def create_album(self, title):
        return self.service.albums().create(body={"album": {"title": title}}).execute()

    def share_album(self, album_id):
        return self.service.albums().share(albumId=album_id).execute()

    def create_shared_album(self, title):
        album_response = self.create_album(title)
        return self.share_album(album_response["id"])

    def get_shared_albums(self):
        return [SharedAlbum(service=self.service, **item) for item in
                self.service.sharedAlbums().list(pageSize=50).execute()["sharedAlbums"]]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--start-date', type=str, required=False,
                        help='initial date for file range')
    parser.add_argument('--end-date', type=str, required=False,
                        help='end date for file range')
    parser.add_argument('--album-names', type=str, nargs="*", required=False,
                        help='which albums to download')

    args = parser.parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date is not None else datetime.datetime(2000, 1, 1)
    end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d")  if args.end_date is not None else None
    print(start_date, end_date)

    photos_api = PhotosApi()
    print(args.album_names)
    print([album.title for album in photos_api.get_shared_albums()])
    shared_albums = [album for album in photos_api.get_shared_albums() if album.title in args.album_names]
    print([album.title for album in shared_albums])

    for album in shared_albums:
        print(f"downloading from {album.title}")
        album.download_and_rename(Config.path + "/google_photo_downloads/")
    print("done!")
