# Define custom utilities
# Test for OSX with [ -n "$IS_OSX" ]

function pre_build {
    # Any stuff that you need to do before you start building the wheels
    # Runs in the root directory of this repository.
    :
}

function run_tests {
    # The function is called from an empty temporary directory.
    cd ..

    # Get absolute path to the pre-compiled wheel
    wheelhouse=$(abspath wheelhouse)
    wheel=$(ls ${wheelhouse}/openstep_plist*.whl | head -n 1)
    if [ ! -e "${wheel}" ]; then
        echo "error: can't find wheel in ${wheelhouse} folder" 1>&2
        exit 1
    fi

    # select tox environment based on the current python version
    # E.g.: '2.7' -> 'py27'
    TOXENV="py${MB_PYTHON_VERSION//\./}-nocov"

    # Install pre-compiled wheel and run tests against it
    tox --installpkg "${wheel}" -e "${TOXENV}"
}

# Custom functions to temporarily pin wheel to 0.31.1
if [ -n "$IS_OSX" ]; then
    function before_install {
        brew cask uninstall oclint || true
        export CC=clang
        export CXX=clang++
        get_macpython_environment $MB_PYTHON_VERSION venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install wheel==0.31.1
    }
else
    function build_wheel_cmd {
        local cmd=${1:-pip_wheel_cmd}
        local repo_dir=${2:-$REPO_DIR}
        [ -z "$repo_dir" ] && echo "repo_dir not defined" && exit 1
        local wheelhouse=$(abspath ${WHEEL_SDIR:-wheelhouse})
        start_spinner
        if [ -n "$(is_function "pre_build")" ]; then pre_build; fi
        stop_spinner
        if [ -n "$BUILD_DEPENDS" ]; then
            pip install $(pip_opts) $BUILD_DEPENDS
        fi
        /opt/python/cp36-cp36m/bin/pip3 install wheel==0.31.1
        (cd $repo_dir && $cmd $wheelhouse)
        pip show wheel
        repair_wheelhouse $wheelhouse
    }
fi
