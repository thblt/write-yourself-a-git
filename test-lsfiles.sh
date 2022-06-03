


wyag="../wyag"
DIR="lsfiles"
mkdir ${DIR}
cd ${DIR}

# Init
${wyag} init .

# create new files
echo "hello world" > hello.txt
echo "fuck world" > fuck.txt

# git add
git add -A

# ls-files
${wyag} ls-files

cd -
rm -rf ${DIR}
