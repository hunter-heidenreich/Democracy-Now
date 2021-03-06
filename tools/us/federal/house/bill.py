import re
import json
from datetime import datetime

from bs4 import BeautifulSoup

from utils import download_file, get_bill_urls


class Bill:
    """
    Representation of a a bill, as adapted
    from the Congressional website.
    While currently fitted for the Federal
    House of Representatives in the USA
    this format may very well fit Senate bills as well.
    """

    ROOT_DIR = 'data/us/federal/house/bills/'
    ROOT_URL = 'https://www.congress.gov'

    def __init__(self, url=None, filename=None):

        self.title = None  # The title of the bill
        self._congress = None  # The congressional session

        # The location of data sources
        # - url  -> original url scraped
        # - html -> cached html on file system
        # - json -> will link to JSON on file system
        self._sources = {}

        # Overview information available from the sources
        self._overview = {}

        # Progress of bill
        self._bill_progress = {}

        self.title_info = []

        self._action_overview = []
        self._actions = []

        self._cosponsors = []

        self._committees = []

        self._related = []

        self.subjects = {}

        self.summary = ''

        self._text = ''

        self._amendments = []

        self._cost_estimates = []

        if url:
            self.load_from_url(url)
        elif filename:
            self.from_json(filename)
        else:
            raise ValueError('ValueError: Unspecified bill source.')

    def __repr__(self):
        return self.title

    def load_from_url(self, url, force_reload=False):
        """
        Given a URL, this will generate the values
        for the Bill from the HTML

        :param url: The URL where the data can be found -- str
        :param force_reload: When True, this will force a refresh of that HTML
        """
        cache = url.split('://')[-1].replace('/', '_')

        self._sources['url'] = url
        self._sources['html'] = self.ROOT_DIR + 'web/' + cache

        data = download_file(self._sources['url'], self._sources['html'], force_reload)
        soup = BeautifulSoup(data, 'html.parser')

        self.title = next(
            soup.find('h1', attrs={'class': 'legDetail'}).strings)
        self.title = self.title[34:]
        self.title = self.title.split(' - ')[0]

        span = soup.find('h1', attrs={'class': 'legDetail'}).find('span')
        timing = next(span.strings)
        if re.search('\d{3}', timing):
            self._congress = int(re.search('\d{3}', timing).group())

        overview = soup.find('div', attrs={'class': 'overview'})
        self._extract_overview(overview)

        progress = soup.find('ol', attrs={'class': 'bill_progress'})
        self._extract_bill_progress(progress)

        titles = soup.find('div', attrs={'id': 'titles-content'})
        self._extracttitle_info(titles)

        act_overview = soup.find('div', attrs={'id': 'actionsOverview-content'})
        self._extract_action_overview(act_overview)

        actions = soup.find('div', attrs={'id': 'allActions-content'})
        self._extract_actions(actions)

        cos = soup.find('div', attrs={'id': 'cosponsors-content'})
        self._extract_cosponsors(cos)

        com = soup.find('div', attrs={'id': 'committees-content'})
        self._extract_committees(com)

        related = soup.find('table', attrs={'class': 'relatedBills'})
        self._extract_related(related)

        subs = soup.find('div', attrs={'id': 'subjects-content'})
        self._extract_subjects(subs)

        summ = soup.find('div', attrs={'id': 'latestSummary-content'})
        self._extract_summary(summ)

        self._extract_text()

        self._extract_amendments()

        costs = soup.find('div', attrs={'id': 'cboEstimate'})
        self._extract_cost(costs)

        self.to_json()

    def _extract_overview(self, overview):
        """
        Given a BeautifulSoup HTML overview extracted
        from a webpage of a Bill, this function will extract
        the available data

        :param overview: The overview box - BeautifulSoup
        """
        for i, tr in enumerate(overview.find_all('tr')):
            th = tr.find('th').text
            if th == 'Sponsor:':

                intro = list(tr.find('td').strings)[-1]
                intro = re.search('\d{2}\/\d{2}\/\d{4}', intro)
                if intro:
                    try:
                        a = tr.find('a')
                        text = a.text.strip().split()
                        self._overview['sponsor'] = {
                            'url': self.ROOT_URL + a.get('href'),
                            'name': ' '.join(text[1:]),
                            'title': text[0],
                            'date': datetime.strptime(intro.group(),
                                                      '%m/%d/%Y').timestamp()
                        }
                    except AttributeError:
                        text = 'No sponsor'
                        self._overview['sponsor'] = {
                            'name': text,
                            'date': datetime.strptime(intro.group(),
                                                      '%m/%d/%Y').timestamp()
                        }
                else:
                    import pdb
                    pdb.set_trace()
            elif th == 'Committees:':
                td = tr.find('td').text
                if 'House' in td:
                    houses = td.split(' | ')
                    house = houses.pop()
                    while 'House' not in house:
                        house = houses.pop()
                    committees = house.split('House - ')[-1].split(';')
                    self._overview['committees'] = \
                        list(map(lambda s: s.strip(), committees))
            elif th == 'Committee Reports:':
                a = tr.find('td').find('a')
                self._overview['committee_report'] = {
                    'url': self.ROOT_URL + a.get('href'),
                    'report': a.text
                }
            elif th == 'Latest Action:' or th == 'Latest Action (modified):':
                temp = tr.find('td').text.strip()
                temp = temp.split('\xa0')[0].strip()
                temp = temp.split('(TXT | PDF)')[0].strip()
                self._overview['latest_action'] = temp

            elif th == 'Roll Call Votes:':
                tds = list(tr.find('td').strings)
                self._overview['roll call count'] = int(tds[-1].split(' ')[0])
            elif th == 'Committee Meetings:':
                self._overview['meetings'] = []
                for a in tr.find('td').find_all('a'):
                    t = a.text
                    if t == '(All Meetings)':
                        continue

                    check = int(t.split(' ')[-1].split(':')[0])
                    if check < 10:
                        chunks = t.split(' ')
                        t = chunks[0] + ' 0' + chunks[1]

                    dt = datetime.strptime(t, '%m/%d/%y %I:%M%p')
                    dt = dt.timestamp()
                    self._overview['meetings'].append({
                        'url': self.ROOT_URL + a.get('href'),
                        'datetime': dt
                    })
            elif th == 'Notes:':
                # TODO: Consider handling this differently
                # Right now, this seems to not occur for many bills
                # so it doesn't seem to relevant to write excessive code
                # for handling what's contained here,
                # other than grabbing the text
                self._overview['notes'] = tr.find('td').text
            else:
                print('New Overview in Bill Identified!')
                import pdb
                pdb.set_trace()

    def _extract_bill_progress(self, progress):
        """
        Extracts the information contained in the HTML progress bar

        :param progress: The HTML of the progress bar
        """
        # label to state
        states = {
            'passed': 1,
            'selected': 0
        }

        for li in progress.find_all('li'):
            text = next(li.strings)
            classes = li.get('class')

            if not classes:
                classes = []

            self._bill_progress[text] = -1
            for c in classes:
                if c in states:
                    self._bill_progress[text] = states[c]

    def _extracttitle_info(self, titles):
        """
        Extracts all title information from a bill

        :param titles: The div containing the title information
        """

        # Short title portion
        short = titles.find('div', attrs={'class': 'shortTitles'})
        try:
            t = None
            for i, child in enumerate(short.children):
                if i % 2 == 1:
                    if i == 3:
                        t = child.text
                    elif i == 5:
                        self.title_info.append({
                            'type': 'short',
                            'title': child.text,
                            'location': t,
                            'chamber': None
                        })
        except AttributeError:
            pass

        sub = titles.find('div', attrs={'class': 'titles-row'})

        hc = sub.find('div', attrs={'class': 'house-column'})
        if hc:
            h4s = list(hc.find_all('h4'))[1:]
            for h4 in h4s:
                self.title_info.append({
                    'type': 'short',
                    'title': h4.next_sibling.next_sibling.text.strip(),
                    'location': h4.text,
                    'chamber': 'House'
                })

        sc = sub.find('div', attrs={'class': 'senate-column'})
        if sc:
            h4s = list(sc.find_all('h4'))[1:]
            for h4 in h4s:
                self.title_info.append({
                    'type': 'short',
                    'title': h4.next_sibling.next_sibling.text.strip(),
                    'location': h4.text,
                    'chamber': 'Senate'
                })

        official = titles.find('div', attrs={'class': 'officialTitles'})

        hc = official.find('div', attrs={'class': 'house-column'})
        if hc:
            h4s = list(hc.find_all('h4'))[1:]
            for h4 in h4s:
                self.title_info.append({
                    'type': 'official',
                    'title': h4.next_sibling.next_sibling.text.strip(),
                    'location': h4.text,
                    'chamber': 'House'
                })

        sc = official.find('div', attrs={'class': 'senate-column'})
        if sc:
            h4s = list(sc.find_all('h4'))[1:]
            for h4 in h4s:
                self.title_info.append({
                    'type': 'official',
                    'title': h4.next_sibling.next_sibling.text.strip(),
                    'location': h4.text,
                    'chamber': 'Senate'
                })

    def _extract_action_overview(self, overview):
        """
        Extracts the overview of the actions taken on this bill

        :param overview: The action overview div - BeautifulSoup
        """
        for tr in overview.find('tbody').find_all('tr'):
            date = tr.find('td', attrs={'class': 'date'}).text
            date = datetime.strptime(date, '%m/%d/%Y').timestamp()
            action = tr.find('td', attrs={'class': 'actions'}).text
            self._action_overview.append({
                'date': date,
                'action': action
            })

    def _extract_actions(self, actions):
        """
        Extracts the full list of actions on a bill

        :param actions: The div containing the actions - BeautifulSoup
        """
        for tr in actions.find('tbody').find_all('tr'):
            tds = list(tr.find_all('td'))

            dt = tds[0].text.split('-')
            date = dt[0]
            if len(dt) > 1:
                time = dt[1]
                hr, mint = time.split(':')
                if int(hr) < 10:
                    hr = '0' + hr
                time = hr + ':' + mint
            else:
                time = None
            dt = date + '-' + time if time else date
            code = '%m/%d/%Y-%I:%M%p' if time else '%m/%d/%Y'
            dt = datetime.strptime(dt, code).timestamp()

            if len(tds) == 3:
                chamber = tds[1].text
                action = tds[2].text

                self._actions.append({
                    'datetime': dt,
                    'action': action,
                    'chamber': chamber
                })
            elif len(tds) == 2:
                action = tds[1].text

                self._actions.append({
                    'datetime': dt,
                    'action': action
                })

    def _extract_cosponsors(self, cos):
        """
        Extracts the cosponsor information

        :param cos: The div of cosponsors
        """

        tb = cos.find('tbody')
        if tb:
            for tr in tb.find_all('tr'):
                try:
                    co, date = list(tr.find_all('td'))
                    date = datetime.strptime(date.text, '%m/%d/%Y').timestamp()
                    co_text = co.text.strip()
                    co = {
                        'url': co.find('a').get('href'),
                        'rep': co_text[:-1] if co_text[-1] == '*' else co_text,
                        'original': co_text[-1] == '*'
                    }
                    self._cosponsors.append({
                        'date': date,
                        'cosponsors': co
                    })
                except ValueError:
                    if 'withdrawnTbody' == tb.get('id'):
                        co, date1, date2, exp = list(tr.find_all('td'))

                        date1 = datetime.strptime(date1.text,
                                                  '%m/%d/%Y').timestamp()
                        date2 = datetime.strptime(date2.text,
                                                  '%m/%d/%Y').timestamp()
                        co_text = co.text.strip()
                        exp_text = exp.text.strip()

                        co = {
                            'url': 'https://www.congress.gov' + co.find('a').get('href'),
                            'rep': co_text[:-1] if co_text[
                                                       -1] == '*' else co_text
                        }

                        self._cosponsors.append({
                            'date': date1,
                            'date withdrawn': date2,
                            'cosponsors': co,
                            'explanation': exp_text
                        })
                    else:
                        import pdb
                        pdb.set_trace()

    def _extract_committees(self, com):
        """
        Extracts the committee information

        :param com: The div of committees
        """

        tb = com.find('tbody')
        if tb:
            sub = None
            com = None
            for tr in tb.find_all('tr'):
                cls = tr.get('class')
                cs = tr.find('th')
                if cls and 'committee' in cls:
                    com = cs.text
                    sub = None
                elif cls and 'subcommittee' in cls:
                    sub = cs.text

                date, act, rep = list(tr.find_all('td'))
                if date.text.strip():
                    date = datetime.strptime(date.text, '%m/%d/%Y').timestamp()
                else:
                    date = None

                rep = {
                    'url': self.ROOT_URL + rep.find('a').get('href'),
                    'title': rep.text
                } if rep.text and rep else None

                self._committees.append({
                    'subcommittee': sub,
                    'committee': com,
                    'datetime': date,
                    'action': act.text.strip(),
                    'report': rep
                })

    def _extract_related(self, table):
        """
        Extracts related bill data

        :param table: The related table - BeautifulSoup
        """
        if table:
            tb = table.find('tbody')
            for tr in tb.find_all('tr'):
                tds = list(tr.find_all('td'))
                if len(tds) == 5:
                    bill, title, rel, ident, act = list(tr.find_all('td'))
                    self._related.append({
                        'bill': {
                            'title': bill.text.strip(),
                            'url': bill.find('a').get('href')
                        },
                        'title': title.text,
                        'relationship': rel.text,
                        'identified': ident.text,
                        'latest_action': act.text
                    })
                else:
                    while tds:
                        if tds[0].find('a'):
                            # Process full 5
                            bill, title, rel, ident, act = tds[:5]
                            tds = tds[5:]
                        else:
                            # Process 2
                            rel, ident = tds[:2]
                            tds = tds[2:]

                        self._related.append({
                            'bill': {
                                'title': bill.text,
                                'url': bill.find('a').get('href')
                            },
                            'title': title.text,
                            'relationship': rel.text,
                            'identified': ident.text,
                            'latest_action': act.text
                        })

    def _extract_subjects(self, div):
        """
        Extracts subject data

        :param div: The subject div - BeautifulSoup
        """
        nav = div.find('div', attrs={'class': 'search-column-nav'})
        if nav:
            uls = nav.find('ul')
            if uls:
                try:
                    hrefs = list(uls.find_all('a'))
                    self.subjects['main'] = {
                        'title': hrefs[0].text.strip(),
                        'url': hrefs[0].get('href')
                    }
                except IndexError:
                    hrefs = list(uls.find_all('li'))
                    self.subjects['main'] = {
                        'title': hrefs[0].text.strip(),
                    }
        others = div.find('div', attrs={'class': 'search-column-main'})
        if others:
            self.subjects['others'] = []
            for a in others.find_all('a'):
                self.subjects['others'].append({
                    'title': a.text.strip(),
                    'url': self.ROOT_URL + a.get('href')
                })

    def _extract_summary(self, div):
        """
        Extracts the summary of a bill

        :param div: The div containing the summary - BeautifulSoup
        """

        ps = div.find_all('p')
        self.summary = '\n'.join([p.text.strip() for p in ps])

    def _extract_text(self, force_reload=False):
        """
        Extracts the text of a Bill
        """
        text_url = '/'.join(self._sources['url'].split('/')[:-1]) + '/text?format=txt'
        text_html = self.ROOT_DIR + 'web/' + text_url.split('://')[-1].replace('/', '_')

        html = download_file(text_url, text_html, force_reload)

        soup = BeautifulSoup(html, 'html.parser')
        container = soup.find('pre', attrs={'id': 'billTextContainer'})
        try:
            self._text = container.text.strip()
        except AttributeError:
            self._text = ''

    def _extract_amendments(self, force_reload=False):
        """
        Extract amendment data
        :param force_reload: Whether or not to force a refresh
        """
        text_url = '/'.join(
            self._sources['url'].split('/')[:-1]) + '/amendments'
        text_html = self.ROOT_DIR + 'web/' + text_url.split('://')[-1].replace(
            '/', '_')

        html = download_file(text_url, text_html, force_reload)
        soup = BeautifulSoup(html, 'html.parser')

        main = soup.find('div', attrs={'id': 'main'})
        ol = main.find('ol')

        if ol:
            for li in ol.find_all('li', attrs={'class': 'expanded'}):
                amend = None
                purpose = None
                sponsor = None
                latest_act = None
                description = None
                committees = None

                for span in li.find_all('span'):
                    if 'amendment-heading' in span.get('class'):
                        amend = {
                            'title': span.find('a').text,
                            'url': self.ROOT_URL + span.find('a').get('href')
                        }
                    elif span.find('strong').text == 'Purpose:':
                        purpose = list(span.strings)[1].strip()
                    elif span.find('strong').text == 'Sponsor:':
                        try:
                            sponsor = {
                                'name': span.find('a').text.strip(),
                                'url': self.ROOT_URL + span.find('a').get('href')
                            }
                        except AttributeError:
                            sponsor = {
                                'name': list(span.strings)[1].strip(),
                                'url': None
                            }
                    elif span.find('strong').text.strip() == 'Latest Action:':
                        latest_act = span.text.strip()
                    elif span.find('strong').text.strip() == 'Description:':
                        description = list(span.strings)[1].strip()
                    elif span.find('strong').text.strip() == 'Committees:':
                        committees = list(span.strings)[2].strip()

                self._amendments.append({
                    'amendment': amend,
                    'purpose': purpose,
                    'sponsor': sponsor,
                    'latest_action': latest_act,
                    'description': description,
                    'committees': committees
                })

    def _extract_cost(self, div):
        """
        Extract cost estimates

        :param div: The div that should contain this information
        """
        pass

    def refresh(self):
        """
        Does a soft refresh of the HTML content
        """
        self.load_from_url(url=self._sources['url'])
        self.to_json()

    def to_json(self):
        """
        Dumps the Bill to a JSON readable format
        """
        filename = '{}_{}.json'.format(self._congress,
                                       self.title.split(' - ')[0])

        json.dump({
            'title': self.title,
            'congress': self._congress,
            'sources': self._sources,
            'overview': self._overview,
            'progress': self._bill_progress,
            'title_info': self.title_info,
            'action_overview': self._action_overview,
            'actions': self._actions,
            'cosponsors': self._cosponsors,
            'committees': self._committees,
            'related_bills': self._related,
            'subjects': self.subjects,
            'summary': self.summary,
            'text': self._text,
            'amendments': self._amendments,
            'cost': self._cost_estimates
        }, open(self.ROOT_DIR + 'json/' + filename, 'w+'))

    def from_json(self, filename):
        """
        Given a filename, reads a JSON formatted Bill
        into a Bill object

        :param filename: The location on the local disk - str
        """
        data = json.load(open(filename))
        self.title = data['title']
        self._congress = data['congress']
        self._sources = data['sources']
        self._overview = data['overview']
        self._bill_progress = data['progress']
        self.title_info = data['title_info']
        self._action_overview = data['action_overview']
        self._actions = data['actions']
        self._cosponsors = data['cosponsors']
        self._committees = data['committees']
        self._related = data['related_bills']
        self.subjects = data['subjects']
        self.summary = data['summary']
        self._text = data['text']
        self._amendments = data['amendments']
        self._cost_estimates = data['cost']

    def get_overview(self):
        return self._overview

    def get_progress(self):
        """
        Gets the current progress of the bill
        """
        for k, v in self._bill_progress.items():
            if v == 0:
                return k

    def get_subjects(self):
        return self.subjects

    def get_congress(self):
        return self._congress

    def get_introduced_date(self):
        intro = datetime.fromtimestamp(self.get_overview()['sponsor']['date'])
        return '{}/{}/{}'.format(intro.month, intro.day, intro.year)
    
    def __hash__(self):
        try:
            return hash(self._sources['url'])
        except KeyError:
            return 0

    def search(self, key, value):
        """
        Given a key/property and an intended value,
        returns True if this bill has the intended value
        :param key: A string property
        :param value: The value searched for
        :return: True or False if this rep is part of the search
        """

        if key == 'source':
            return value in self._sources.values()
        elif key == 'title':
            value = value.replace(' ', '.')
            return value.lower() == self.title.lower()
        elif key == 'congress':
            return value == self._congress
        elif key == 'sponsor url':
            if 'sponsor' in self._overview and 'url' in self._overview['sponsor']:
                return value == self._overview['sponsor']['url']
        elif key == 'cosponsor url':
            return value in [co['cosponsors']['url'] for co in self._cosponsors]
        else:
            print('Unknown property for bill. Returning False')

        return False


if __name__ == '__main__':
    from tqdm import tqdm
    new, old = get_bill_urls()
    for f in tqdm(new):
        Bill(url=f)
    # for f in tqdm(old):
    #     Bill(url=f).refresh()
