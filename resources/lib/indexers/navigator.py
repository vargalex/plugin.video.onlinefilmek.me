# -*- coding: utf-8 -*-

'''
    dmdamedia Addon
    Copyright (C) 2020

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os,sys,re,xbmc,xbmcgui,xbmcplugin,xbmcaddon,base64,time, locale
import resolveurl as urlresolver
from resources.lib.modules import client
from resources.lib.modules.utils import py2_encode, py2_decode

if sys.version_info[0] == 3:
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus


sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'https://online-filmek.me/'
helperStr = 'ZYYZOTUuMTExLjIzMC4xNDI6MzEyOAZZWZWZZZYYYZZ'

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass
        self.base_path = py2_decode(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")
        self.helper = helperStr.replace("Z", "").replace("W", "S")

    def getRootMenu(self):
        self.addDirectoryItem('Filmek', 'moviecategories', '', 'DefaultFolder.png')
        self.addDirectoryItem('Sorozatok', 'ordertypes&url=%ssorozatok/legfrissebb/1' % base_url, '', 'DefaultFolder.png')
        self.addDirectoryItem('Keresés', 'search', '', 'DefaultFolder.png')
        self.endDirectory()

    def getMovieCategories(self):
        url_content = client.request(base_url)
        filmekMenu = client.parseDOM(url_content, 'ul', attrs={'class': 'dropdown-menu'})[0]
        categories = client.parseDOM(filmekMenu, 'li')
        for category in categories:
            url = client.parseDOM(category, 'a', ret='href')[0]
            title = client.parseDOM(category, 'a')[0]
            if title != "Sorozatok":
                self.addDirectoryItem(title, 'ordertypes&url=%s' % url, '', 'DefaultFolder.png')
        self.endDirectory()

    def getOrderTypes(self, url):
        url_content = client.request(url)
        buttons = client.parseDOM(url_content, 'div', attrs={'class': 'buttons'})[0]
        orders = buttons.replace('</a>', '</a>\n')
        for order in orders.splitlines():
            matches = re.search(r'<a href="([^"]*)"(.*)</i>(.*)</a>$', order.strip())
            if matches:
                self.addDirectoryItem(matches.group(3), 'movies&url=%s' % (matches.group(1) if matches.group(1) != "#" else url), '', 'DefaultFolder.png')
        self.endDirectory()

    def getMovies(self, url):
        url_content = client.request(url)
        movies = client.parseDOM(url_content, 'div', attrs={'class': 'thumbnail-container'})
        for movie in movies:
            url = client.parseDOM(movie, 'a', ret='href')[0]
            thumb = client.parseDOM(movie, 'img', attrs={'loading': 'lazy'}, ret='src')[0]
            title = client.parseDOM(movie, 'span', attrs={'class': 'title-text'})[0]
            self.addDirectoryItem(title, ('movie&url=%s' % url) if "sorozat" not in url else ('sorozat&url=%s' % url), thumb, 'DefaultMovies.png', meta={'title': title, 'fanart': thumb})
        buttons = client.parseDOM(url_content, 'div', attrs={'class': 'buttons'})
        if len(buttons)>1:
            pages = buttons[1].replace('</a>', '</a>\n').splitlines()
            if "következő oldal" in py2_encode(pages[len(pages)-1]):
                matches = re.search(r'<a href="([^"]*)"(.*)$', pages[len(pages)-1])
                if matches:
                    self.addDirectoryItem("[I]Következő oldal >>[/I]", 'movies&url=%s' % (matches.group(1)), '', 'DefaultFolder.png')

        self.endDirectory()

    def getSearches(self):
        self.addDirectoryItem('Új keresés', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                self.addDirectoryItem(item, 'movies&url=%skereses.php?kereses=%s' % (base_url, quote_plus(item)), '', 'DefaultFolder.png')
            if len(items) > 0:
                self.addDirectoryItem('Keresési előzmények törlése', 'deletesearchhistory', '', 'DefaultFolder.png') 
        except:
            pass   
        self.endDirectory()

    def deleteSearchHistory(self):
        if xbmcgui.Dialog().yesno("Megerősítés", "Biztosan törli a keresési előzményeket?"):
            if os.path.exists(self.searchFileName):
                os.remove(self.searchFileName)

    def doSearch(self):
        search_text = self.getText(u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write("%s\n" % search_text)
            file.close()
            self.getMovies("%skereses.php?kereses=%s" % (base_url, quote_plus(search_text)))


    def getResults(self, search_text):
        url_content = client.request(base_url)
        searchDiv = client.parseDOM(url_content, 'div', attrs={'id': 'search'})
        innerFrameDiv = client.parseDOM(searchDiv, 'div', attrs={'class': 'inner_frame'})
        searchURL = client.parseDOM(innerFrameDiv, 'form', ret='action')[0]
        uid = client.parseDOM(innerFrameDiv, 'input', attrs={'id': 'uid'}, ret='value')[0]
        url_content = client.request(searchURL, post="uid=%s&key=%s" % (uid, quote_plus(search_text)))
        searchResult = client.parseDOM(url_content, 'div', attrs={'class': 'search-results'})
        resultsUser = client.parseDOM(searchResult, 'div', attrs={'class': 'results-user'})
        ul = client.parseDOM(resultsUser, 'ul')
        if len(ul)>0:
            lis = client.parseDOM(ul, 'li')
            for li in lis:
                href = client.parseDOM(li, 'a', ret='href')[0].replace('http://', 'https://').replace(base_url, '')
                if "filmkeres-es-hibas-link-jelentese.html" not in href:
                    title = py2_encode(client.parseDOM(li, 'a')[0])
                    self.addDirectoryItem(title, 'movie&url=%s' % quote_plus(href), '', 'DefaultMovies.png')
            self.endDirectory('movies')
        else:
            xbmcgui.Dialog().ok("OnlineFilmvilág2", "Nincs találat!")

    def getSources(self, url):
        url_content = client.request(url)
        title = client.parseDOM(url_content, 'h1')[0]
        thumb = client.parseDOM(url_content, 'img', attrs={'class': 'kep_meret'}, ret='src')[0]
        plot = py2_encode(client.replaceHTMLCodes(client.parseDOM(url_content, 'div', attrs={'class': 'leiras'})[1])).replace("<h3>Leirás</h3>", "")
        sourceCnt = 0
        linkektables = client.parseDOM(url_content, 'table', attrs={'id': 'linkek'})
        for linkektable in linkektables:
            tbody = client.parseDOM(linkektable, 'tbody')[0]
            sorok = client.parseDOM(tbody, 'tr')
            for sor in sorok:
                oszlopok = client.parseDOM(sor, 'td')
                srcHost = oszlopok[1].replace('<b>','').replace('</b>', '')
                matches = re.search(r'<div class="([^"]*)"></div>(.*)$', oszlopok[0])
                url = client.parseDOM(sor, 'a', ret='href')[0]
                minoseg = ""
                szinkron = ""
                if matches:
                    minoseg = " | [I]%s[/I]" % matches.group(2)
                    if "feirat" in matches.group(1):
                        szinkron = " | [I]feliratos[/I]"
                    else:
                        if "eredeti" in matches.group(1):
                            szinkron = " | [I]eredeti nyelv[/I]"
                egyeb = ""
                if oszlopok[2] != "":
                    egyeb = "[I] (%s)[/I]" % oszlopok[2]
                sourceCnt+=1
                self.addDirectoryItem('%s | [B]%s[/B]%s%s%s' % (format(sourceCnt, '02'), srcHost, minoseg, szinkron, egyeb), 'playmovie&url=%s&host=%s' % (url, srcHost), thumb, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'banner': thumb})
        self.endDirectory('movies')
    
    def getMovie(self, url):
        url_content = client.request(url)
        if "megoszto_link" not in url_content:
            xbmc.log("onlinefilmek.me: megoszto_link not in page using proxy: %s " % base64.b64decode(self.helper.replace("S", "=").replace("Y", "").encode('ascii')).decode('ascii'), xbmc.LOGINFO)
            url_content = client.request(url.replace("https", "http"), proxy=base64.b64decode(self.helper.replace("S", "=").replace("Y", "").encode('ascii')).decode('ascii'))
        sourcesUrl = client.parseDOM(url_content, 'a', attrs={'id': 'megoszto_link'}, ret='href')[0]
        self.getSources(sourcesUrl)

    def getEpisodes(self, url):
        url_content = client.request(url)
        title = client.parseDOM(url_content, 'h1', attrs={'class': 'title'})[0]
        title = client.parseDOM(title, 'span')[0]
        thumb = client.parseDOM(url_content, 'img', attrs={'class': 'poster'}, ret='src')[0]
        plot = client.replaceHTMLCodes(client.parseDOM(url_content, 'p', attrs={'itemprop': 'description'})[0])
        if "megoszto_link" not in url_content:
            xbmc.log("onlinefilmek.me: megoszto_link not in page using proxy: %s " % base64.b64decode(self.helper.replace("S", "=").replace("Y", "").encode('ascii')).decode('ascii'), xbmc.LOGINFO)
            url_content = client.request(url.replace("https", "http"), proxy=base64.b64decode(self.helper.replace("S", "=").replace("Y", "").encode('ascii')).decode('ascii'))
        episodes = client.parseDOM(url_content, 'div', attrs={'class': 'buttons buttons2'})[0].replace("</a>", "</a>\n")
        for episode in episodes.splitlines():
            matches = re.search(r'<a href="([^"]*)"(.*)>(.*)</a>(.*)', episode)
            if matches:
                self.addDirectoryItem(matches.group(3), 'sources&url=%s' % matches.group(1), thumb, 'DefaultMovies.png', meta={'title': title, 'plot': plot, 'banner': thumb})
        self.endDirectory('episodes')

    def playmovie(self, url, host):
        xbmc.log('onlinefilmek.me: resolving onlinefilmek.me url: %s' % url, xbmc.LOGINFO)
        url_content = client.request(url)
        mainContainer = client.parseDOM(url_content, 'div', attrs={'id': 'main_container'})[0]
        script = (u'%s' % client.parseDOM(mainContainer, 'script')[0])
        matches = re.search(r"var(.*)=\['([^']*)(.*)$", script)
        if matches:
            encoded = matches.group(2)
            replaces = re.findall("_0x418837=_0x418837\['replace'\]\(([^\)]*)\)", script, re.S)
            for replace in replaces:
                encoded = encoded.replace(replace[1], replace[6])
            iFrame = base64.b64decode(encoded.encode('ascii')).decode('ascii')
            url = client.parseDOM(iFrame, 'iframe', ret='src')[0]
            xbmc.log('onlinefilmek.me: founded url: %s, trying to resolve' % url, xbmc.LOGINFO)
            try:
                direct_url = urlresolver.resolve(url)
                if direct_url:
                    direct_url = py2_encode(direct_url)
                else:
                    direct_url = url
            except Exception as e:
                xbmcgui.Dialog().notification(host, str(e))
                return
            if direct_url:
                xbmc.log('onlinefilmek.me: playing URL: %s' % direct_url, xbmc.LOGINFO)
                play_item = xbmcgui.ListItem(path=direct_url)
                xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
        else:
            xbmcgui.Dialog().notification(host, "Script not founded")

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        if thumb == '': thumb = icon
        cm = []
        if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
        if not context == None: cm.append((py2_encode(context[0]), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart == None: Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if isFolder == False: item.setProperty('IsPlayable', 'true')
        if not meta == None: item.setInfo(type='Video', infoLabels = meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)


    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)

    def getText(self, title, hidden=False):
        search_text = ''
        keyb = xbmc.Keyboard('', title, hidden)
        keyb.doModal()

        if (keyb.isConfirmed()):
            search_text = keyb.getText()

        return search_text
