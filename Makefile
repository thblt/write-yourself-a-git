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
    -f org-html-export-to-html

wyag libwyag.py: write-yourself-a-git.org
	emacs --batch write-yourself-a-git.org -f org-babel-tangle

clean:
	rm -f wyag libwyag.py write-yourself-a-git.html .last_push

test: wyag libwyag.py
	./wyag-tests.sh

.last_push: write-yourself-a-git.html
	 scp -r write-yourself-a-git.html k9.thb.lt\:/var/www/wyag.thb.lt/index.html; \
   scp -r lib/org-html-themes/src k9.thb.lt:/var/www/wyag.thb.lt/; \
   touch .last_push
