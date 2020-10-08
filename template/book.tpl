\begin{center}
    \poemtitle{$$ title $$}
    $$ subtitle $$
\end{center}


$$ argument $$

\newpage

\settowidth{\versewidth}{Instruct me, for Thou know'st; Thou from the first}
\poemlines{10}
\begin{verse}[\versewidth]

{%- for paragraph in main %}
$$ paragraph $$

{% endfor %}

\end{verse}

$$ end $$