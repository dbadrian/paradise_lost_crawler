\documentclass{article}

\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{verse, anyfontsize} % load before hyperref!
\usepackage{hyperref}
\usepackage{lettrine}
\usepackage{scalerel}
\usepackage{stackengine}
\usepackage{ruby}
\usepackage{relsize,etoolbox}% http://ctan.org/pkg/{relsize,etoolbox}

\setlength{\parindent}{0pt} % Disable paragraph indentation
\AtBeginEnvironment{quote}{\smaller}% Step font down one size relative to current font.

\renewcommand{\poemtitlefont}{\normalfont\bfseries\Huge\centering} % Define the poem title style
\setlength{\stanzaskip}{0.75\baselineskip} % The distance between stanzas

\renewcommand{\footnotesize}{\fontsize{5pt}{5pt}\selectfont}

\usepackage{quoting}
\quotingsetup{vskip=3pt}

{% if disable_modern_spelling %}
% Hide modern spelling
{% raw -%}
\renewcommand{\ruby}[2]{#1}
{% endraw %}
{% elif force_modern_spelling %}
% Replace old terms with modern spelling
{% raw -%}
\renewcommand{\ruby}[2]{#2}
{% endraw %}
{% endif %}

{% if disable_annotations %}
% Hide footnotes
\renewcommand{\footnote}[2][]{\relax}
{% endif %}

\begin{document}
\input{content}	
\end{document} 
