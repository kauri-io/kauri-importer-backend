# docsupport

![](https://github.com/wilbarnes/docsupport/blob/master/gh-to-kauri-export.jpg)

in progress:
* writing code to move the markdown source files to kauri dev into draft state
* understand messaging signing needs, if needed, github authentication, attribution
* webhook from GH
* need to understand implications of documentation licensing


right now the code is lightweight with no external libraries

with the below command you can clone the repo, setup basic directories, find and parse the mkdocs.yml file into an indexed dictionary to send to kauri new collection. the index is designed so that we'll be able to layout the files as they would be in mkdocs or any other doc builder
```
$ python3 main.py -r <insert-mkdocs-based-project-here>
```

for example (in terminal):
```
python3 main.py -r https://github.com/wilbarnes/smart-contract-best-practices
```

the output looks weird because it's using python's prettyprint library for debugging, which prints the dicts in alphabetic order
