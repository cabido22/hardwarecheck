"""
Script to turn INI files in to a browsable HTML tree. I thought this might make helpful 
for large .res files, or some of the other debug info...We'll see...

Code taken from:

http://wwwendt.de/tech/dynatree/doc/samples.html

"""
from components.utils import orderedConfigParser as ConfigParser
import os 
import json

_header_for_html = None # fill in later

def ini2html(ini,html):
    if not os.path.exists(ini):
        raise Exception("ini file %s missing"%ini)

    if not os.path.exists(os.path.dirname(html)):
        raise Exception("html directory for output file %s missing"%html)

    parser = ConfigParser()
    parser.readfp( open(ini) )
    outf = open(html,"w")
    outf.write("<html>\n")
    outf.write(_header_for_html)
    body = []
    for snum,section in enumerate(parser.sections()):
        body.append('<li id="id{0}" class="folder">{1}<ul>'.format(snum,section))
        for inum,item in enumerate(parser.items(section)):
            body.append('<li id="id{0}.{1}">{2} : {3}'.format(snum,inum,item[0],item[1]))
        body.append("</ul>")

    body = "\n".join(body)
    outf.write("""
<body class="example">
  <div id="tree">
    <ul id="treeData" style="display: none;">
    %s
    </ul>
  </div>
</body>
    """%body)
    outf.write("</html>\n")


_header_for_html = """
<head>
  <meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
  <title>Dynatree - Example</title>
 
  <script type='text/javascript' src='http://code.jquery.com/jquery-1.5.2.js'></script>
  <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.9/jquery-ui.js"></script>
  
  
  <link rel="stylesheet" type="text/css" href="/css/result-light.css">
   <script type='text/javascript' src="http://dynatree.googlecode.com/svn/trunk/src/jquery.dynatree.js"></script>
   <link rel="stylesheet" type="text/css" href="http://wwwendt.de/tech/dynatree/src/skin-vista/ui.dynatree.css">

  <!-- (Irrelevant source removed.) -->

  <script type="text/javascript">
    $(function(){
      $("#tree").dynatree({
        // using default options
      });
      <!-- (Irrelevant source removed.) -->
    });
  </script>
</head>
"""

def ini2htmljson(ini,jsonpath,nohtml=False):
    if not os.path.exists(ini):
        raise Exception("ini file %s missing"%ini)

    if not os.path.exists(os.path.dirname(jsonpath)):
        raise Exception("jsonpath directory for output file %s missing"%jsonpath)

    parser = ConfigParser()
    parser.readfp( open(ini) )
    outf = open(jsonpath,"w")
    body = []
    body.append("[")
    for snum,section in enumerate(parser.sections()):
        body.append('\t{"title":"%s", "isFolder":true ,"key":"folder%s",'%(section,snum))
        items = parser.items(section)
        if len(items)==0: # ?
            body[-1] = body[-1][:-1] # remove comma
            continue
        body.append('\t\t"children":[')
        for inum,item in enumerate(parser.items(section)):
            body.append('\t\t\t{"title":"%s=%s"},'%(item[0],item[1]))
        body[-1] = body[-1][:-1] # remove comma
        body.append("\t\t\t]")
        body.append("\t\t},")
    body[-1] = body[-1][:-1] # remove comma
    body.append("]")

    body = "\n".join(body)
    outf.write(body)
    outf.close()
    # now write out the HTML portion and point it to json
    htmlf = os.path.dirname(jsonpath) + os.sep + os.path.basename(jsonpath) + ".html"
    outf = open(htmlf,"w")
    outtext = _html_tree_with_json%(os.path.basename(jsonpath))
    outf.write(outtext)
    outf.close()

_html_tree_with_json = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
  <meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
  <title>Dynatree - Example</title>

  
  <script type='text/javascript' src='http://code.jquery.com/jquery-1.5.2.js'></script>
  <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.9/jquery-ui.js"></script>
  
  
  <link rel="stylesheet" type="text/css" href="/css/result-light.css">
   <script type='text/javascript' src="http://dynatree.googlecode.com/svn/trunk/src/jquery.dynatree.js"></script>
   <link rel="stylesheet" type="text/css" href="http://wwwendt.de/tech/dynatree/src/skin-vista/ui.dynatree.css">
    
    

  <!-- (Irrelevant source removed.) -->

<script type="text/javascript">
  $(function(){
    $("#tree").dynatree({
      // In real life we would call a URL on the server like this:
//          initAjax: {
//              url: "/getTopLevelNodesAsJson",
//              data: { mode: "funnyMode" }
//              },
      // .. but here we use a local file instead:
      initAjax: {
        url: "%s"
        },
      onActivate: function(node) {
        $("#echoActive").text(node.data.title);
      },
      onDeactivate: function(node) {
        $("#echoActive").text("-");
      }
    });
  });
</script>
</head>

<body class="example">
  <!-- Add a <div> element where the tree should appear: -->
  <div id="tree">  </div>

  <div>Active node: <span id="echoActive">-</span></div>

  <!-- (Irrelevant source removed.) -->
</body>
</html>


"""


def json2html(json_file, html):
    """ Function to read json file and export to html - Carlos"""
    if not os.path.exists(json_file):
        raise Exception("JSON file %s missing" % json_file)

    if not os.path.exists(os.path.dirname(html)):
        raise Exception("HTML directory for output file %s missing" % html)

    with open(json_file, "r") as file:
        data = json.load(file)

    with open(html, "w") as outf:
        outf.write("<html>\n")
        outf.write(_header_for_html)
        body = []

        for snum, section in enumerate(data):
            body.append('<li id="id{0}" class="folder">{1}<ul>'.format(snum, section))
            for inum, item in enumerate(data[section]):
                body.append('<li id="id{0}.{1}">{2} : {3}'.format(snum, inum, item, data[section][item]))
            body.append("</ul>")

        body = "\n".join(body)
        outf.write(body)
