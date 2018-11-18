
import subprocess
import json
import json2html
import time
from datetime import datetime

from run_project import db, Website

def run_scan(url):
    url = 'http://' + url
    name = url.replace('.','').replace(':','').replace('/','')

    bash = subprocess.Popen("wapiti {} -n 10 -u -v 1 -f json -o {}.json".format(url, name),
                   shell=True,
                   cwd='/mnt/d/Users/Franco/Documents/PI_2/src/reports') # Gera o json na pasta reports (usando no subsystem de linux)
    while True:
        poll = bash.poll()

        if poll is None:
            time.sleep(60)
        else:
            build_html(url, name)
            break

    return '{} scan html report generated successfully'.format(name)

def build_html(url, name):
    #TODO: Deletar o json depois de gerar o html
    html_name = '/mnt/d/Users/Franco/Documents/PI_2/src/reports/'+name+'.html'
    with open('/mnt/d/Users/Franco/Documents/PI_2/src/reports/'+name+'.json', 'r') as f:
        json_info = json.load(f)

    converter = json2html.Json2Html()
    tab_names = list(json_info.keys())

    html_content = ''
    for name in tab_names:
        html_content += """<div class='w3-bar tab-header' onclick='website_details("{}");'><h4>{}</h4></div><div class="tab-container w3-card-4">""".format(name, name)
        html_content += converter.convert(json=json_info[name], table_attributes='id="{}" class="table"'.format(name))
        html_content += '</div>'

    report_html = """"
    <html>
    <head>
    <link rel="stylesheet" href="../static/style.css" />
    <script src="../static/functions.js" type="text/javascript"></script>
    <title>Securite - Report</title>
    </head>
    <body>
    <div class="flex_div row center" style="margin-bottom:30px">
    <img src="../static/logo2.png" class="logo" />
    <h2 class="alert alert-info">Report - {}</h2>
    <button onclick="window.location.href='/manage/'">Voltar</button>
    </div>
    {}
    </html>""".format(url, html_content)

    website = Website.query.filter_by(url=url).first()
    website.updated_at = datetime.now().strftime('%d-%m-%Y %H:%M')
    db.session.commit()

    with open(html_name, "w") as f:
        f.write(report_html)



















