

### Install

#### Install editable
1. `git clone REPO`
1. `cd REPO`
1. `uv tool install --editable .`

#### Or install from wheel
1. `git clone REPO`
1. `cd REPO`
1. `uv tool build`
1. `uv tool install dist/prompt-X.X.X-py3-none-any.whl`

#### Completion
Configure completion for prompt. Add the following to your `.bashrc` or `.bash_profile`.
``` bash
if hash prompt 2>/dev/null; then
    eval "$(_PROMPT_COMPLETE=bash_source prompt)"
fi
```

### Dir teleport

How to set up teleport.

``` bash
function cdd
{
    eval "$(prompt project cd "$1")"
}
# completion for cdd
function _cdd
{
    # the sed removes blank lines and lines starting with a comment (#)
    local cur=${COMP_WORDS[COMP_CWORD]}
    COMPREPLY=(
        $(compgen -W \
          "$(sed "/\(^$\|^#\)/d" < $HOME/.prompt-projects | cut -f1 | sort | xargs)" -- "$cur")
    )
}
complete -F _cdd cdd
```

### PS1 Prompt

``` bash
# load the bash prompt source
function _prompt_command() {
    export PS1="$(prompt ps1)"
}
export PROMPT_COMMAND=_prompt_command
```

### UI

``` bash
prompt ps1
prompt themes
prompt project cd [DIR-NAME]
prompt project add NAME PROJECT-ROOT [COLOUR]
prompt project edit
```


### Edit

``` bash
sudo apt-get install build-essential libgl1-mesa-dev
sudo apt install libcairo2-dev libxt-dev libgirepository1.0-dev
uv add pycairo PyGObject
```
