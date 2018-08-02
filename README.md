# Paradise Lost Crawler

Crawls the content of the more than excellent Dartmouth "The John Milton Reading Room", including the text annotations.
It also converts them into a ready to use tex-formatted version, which allows to easily create a pdf for !PERSONAL USE!.

There are still some "bugs"/missing features, such as specially formatting block-quotes in annotation. Thats future (TM) work...
Currently you need to manually fix four erros in the tex files, takes about 20 seconds :).

# Todo
- [x] Alternative (=modern) spelling (e.g., as "furigana" using ruby)
- [ ] Incorrectly crawled annotations (double, probably due to timing issues with dynamic elements)
- [x] Deal with block quotes in annotations
- [x] Deal with external links
- [ ] Deal with internal links
- [x] Fix weird space+dot punctation in annotations
- [ ] Improved tex template
- [ ] Enable options: generate links, generate overtext modern spellings, etc.

# License
The code itself is under MIT, see repository.

The content it crawls:
[Read the original license information of the reading room.](https://www.dartmouth.edu/~milton/reading_room/copyrights/text.shtml)
