import configparser
import json
import multiprocessing
import os
import bs4
import git
import requests


class GitGetter(multiprocessing.Process):
    def __init__(self, git_path: str, github_url: str, *args, **kwargs):
        self.git_path = git_path
        self.github_url = github_url
        super(GitGetter, self).__init__(*args, **kwargs)

    def pull(self) -> bool:
        """
        perform a git pull on the configured directory. If we had to clone the repo, return true, since changes
        definitely occurred.

        :return: boolean,  whether there were any updates during the git pull
        """
        if not os.path.exists(self.git_path):
            os.mkdir(self.git_path)
            git.Repo.clone_from(self.github_url, self.git_path)
            return True
        else:
            try:
                repo = git.Repo(self.git_path)
            except git.exc.InvalidGitRepositoryError:
                git.Repo.clone_from(self.github_url, self.git_path)
                return True
        current = repo.head.commit
        repo.remotes.origin.pull()
        return current != repo.head.commit

    def run(self) -> None:
        """
        Run one git pull, then return.
        :return: None
        """
        self.pull()


class AptNotesGetter(GitGetter):
    def __init__(self, git_path: str, github_url: str, archive_path: str, *args, **kwargs):
        self.archive_path = archive_path
        super(AptNotesGetter, self).__init__(git_path, github_url, *args, **kwargs)

    def run(self) -> None:
        """
        Slightly more complex process for APT Notes: their github repo contains a json file that contains
        urls to download the reports. So first we do the pull, then if there were changes go through those
        changes and grab any files.

        :return: None
        """
        updated = self.pull()
        if not updated:
            return
        json_file = json.load(open(os.path.join(self.git_path, "APTNotes.json")))
        save_dir = os.path.join(self.git_path, self.archive_path)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        for entry in json_file:
            print(f"working on {entry}")
            target_file_path = os.path.join(save_dir, entry['Filename'])
            if not os.path.exists(target_file_path):
                url = entry['Link']
                self.download_url(target_file_path, url)

    @staticmethod
    def download_url(target_file_path: str, url: str) -> None:
        """
        Download a file from box's shared url.

        Gets the box download capture page, parse it for the real download link, downloads the file from that.
        This is really, really gross, but the only other option with box is an unholy mess of oauth2
        and 60-minute-limited developer tokens.
        :param target_file_path: the path to save the file to
        :param url: the shared url of the box site
        :return: None
        """

        #
        # Built this from the aptnotes tools (one or two of their steps were unnecessary, so I skipped them)
        #
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.content, "html.parser")
        scripts = soup.find_all("script")
        sections = scripts[-1].contents[0]
        json_data = sections.split("=")[1].rstrip(";")
        js_config = json.loads(json_data)
        app_api = js_config['/app-api/enduserapp/shared-item']
        name = app_api['sharedName']
        itemid = app_api['itemID']
        d_url = f"https://app.box.com/index.php?rm=box_download_shared_file&shared_name={name}&file_id=f_{itemid}"
        file_download = requests.get(d_url, stream=True)
        with open(target_file_path, "wb") as filehandle:
            for chunk in file_download.iter_content(8192):
                filehandle.write(chunk)


class CyberMonitorGetter(GitGetter):
    pass


class FdiskYouGetter(GitGetter):
    pass


if __name__ == "__main__":
    configfile = configparser.ConfigParser()
    configfile.read("ti-collector.conf")
    aptnotes_path = configfile.get("APTNotes", "git_path")
    aptnotes_archive_path = configfile.get("APTNotes", "archive_dir", fallback="reports")
    aptnotes_github_url = configfile.get("APTNotes", "github_url")

    apt_cybermonitor_path = configfile.get("APTCyberMonitor", "git_path")
    apt_cybermonitor_github_url = configfile.get("APTCyberMonitor", "github_url")

    fdiskyou_path = configfile.get("FDiskYou", "git_path")
    fdiskyou_github_url = configfile.get("FDiskYou", "github_url")

    aptnotes_getter = AptNotesGetter(aptnotes_path, aptnotes_github_url, aptnotes_archive_path)
    aptnotes_getter.start()

    cyberMonitor_getter = CyberMonitorGetter(apt_cybermonitor_path, apt_cybermonitor_github_url)
    cyberMonitor_getter.start()

    fdiskyou_getter = FdiskYouGetter(fdiskyou_path, fdiskyou_github_url)
    fdiskyou_getter.start()

    aptnotes_getter.join()
    cyberMonitor_getter.join()
    fdiskyou_getter.join()
