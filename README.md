# golinkslite
Go Links Lite

(c) 2019 Robert Muth (GNU General Public License, Version 3)


Go-Links-Lite is a simple URL shortener modelled after similar internal tools 
used by many "tech companies".

Program consists of a single Python 3 file and the only heavy dependency is 
the 'flask' web framework. It does not use authentication and all links are 
shared and editable by everybody. The backend consists of a json text file. 

It is usually configured to run on port 80 on a machine which is known by the 
name "go", so that http://go/TAG or simply go/TAG can be used to abbreviate a 
link.

[History of Go Links](https://medium.com/@golinks/the-full-history-of-go-links-and-the-golink-system-cbc6d2c8bb3)

