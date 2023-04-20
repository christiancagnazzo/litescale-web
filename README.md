# litescale-web

<div align="center">
<img src="static/images/litescale_logo.png"  alt="Litescale" />
<br/><br/>

_A Web application for Best-worst Scaling annotation based on the [Litescale](https://github.com/valeriobasile/litescale) standalone library_

---
</div>

Best-worst Scaling (BWS) is a methodology for annotation based on comparing and ranking instances, rather than classifying or scoring individual instances.
LITESCALE is a free software library to create and manage BWS annotation tasks. It computes the tuples to annotate, manages the users and 
the annotation process, and creates the final gold standard. 
<br></br>
LITESCALE-WEB is a fully online version of Litescale with multi-user support implemented with the _Flask_ Python framework. A RESTful HTTP API is provided 
in order to expose the core library functionalities, and a Web application provides the user interface by connecting to the API.
<br></br>
This project was implemented for my bachelor thesis in Computer Science at the University of Turin. 
Litescale and Litescale Web are described in more detail in the following paper 
[Litescale: A Lightweight Tool for Best-worst Scaling Annotation](https://aclanthology.org/2021.ranlp-1.15) (Basile & Cagnazzo, RANLP 2021).







