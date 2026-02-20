all: article program
article: write-yourself-a-git.html
program: wyag libwyag.py
push: .last_push

.PHONY: all article clean program push test

write-yourself-a-git.html: write-yourself-a-git.org wyag libwyag.py
	emacs --batch write-yourself-a-git.org \
    --eval "(add-to-list 'load-path (expand-file-name \"./lib/htmlize\"))" \
    --eval "(setq org-babel-inline-result-wrap \"%s\")" \
    --eval "(setq org-confirm-babel-evaluate nil)" \
    --eval "(setq python-indent-guess-indent-offset nil)" \
    --eval "(setq org-export-with-broken-links t)" \
		--eval "(setq org-html-htmlize-output-type 'css)" \
    --eval "(org-babel-do-load-languages 'org-babel-load-languages '((dot . t)))" \
    -f org-html-export-to-html

write-yourself-a-git.pdf: write-yourself-a-git.org wyag libwyag.py
	emacs --batch write-yourself-a-git.org \
    --eval "(add-to-list 'load-path (expand-file-name \"./lib/htmlize\"))" \
    --eval "(setq org-babel-inline-result-wrap \"%s\")" \
    --eval "(setq org-confirm-babel-evaluate nil)" \
    --eval "(setq python-indent-guess-indent-offset nil)" \
    --eval "(setq org-export-with-broken-links t)" \
    --eval "(org-babel-do-load-languages 'org-babel-load-languages '((dot . t)))" \
    -f org-latex-export-to-pdf

wyag libwyag.py: write-yourself-a-git.org
	emacs --batch write-yourself-a-git.org -f org-babel-tangle

wyag.zip: wyag libwyag.py LICENSE
	zip -r wyag.zip wyag libwyag.py LICENSE

clean:
	rm -f wyag libwyag.py write-yourself-a-git.html .last_push wyag.zip

test: wyag libwyag.py
	./wyag-tests.sh

.last_push: wyag.zip write-yourself-a-git.html
	scp -r write-yourself-a-git.html k9.thb.lt\:/var/www/wyag.thb.lt/index.html; \
	scp -r *.svg wyag.zip lib/org-html-themes/src k9.thb.lt:/var/www/wyag.thb.lt/; \
	touch .last_push
