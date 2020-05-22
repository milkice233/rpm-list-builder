import yaml


def r(cmd):
    print(cmd)


with open('../python39.yaml') as f:
    pkgs = yaml.safe_load(f)['python39']['packages']


for pkg in pkgs:
    macros = {}
    replaced = {}

    chaneglog = 'Rebuilt for Python 3.9'
    if isinstance(pkg, dict):
        assert len(pkg) == 1
        chaneglog = 'Bootstrap for Python 3.9'
        for key, val in pkg.items():
            pkg = key
            macros = val.get('macros', {})
            replaced = val.get('replaced_macros', {})

    patch = f'../{pkg}.patch'

    r(f'fedpkg clone {pkg}')
    r(f'cd {pkg}')
    r(f'test -f {patch} && patch -R -p1 < {patch} && rm {patch} '
      f'&& git add {pkg}.spec')
    for macro, value in macros.items():
        r(fr"sed -i '1s;^;%global {macro} {value}\n;' {pkg}.spec")
    for macro, value in replaced.items():
        r(fr"sed -i -r -E 's/%(define|global)(\s+){macro}(\s+)"
          fr"([^\s]+)/%\1\2{macro}\3{value}/' {pkg}.spec")
    if macros or replaced:
        r(f'git diff > {patch}')
    r(f'rpmdev-bumpspec -c "{chaneglog}" {pkg}.spec')
    r(f'git commit -m "{chaneglog}" {pkg}.spec')
    r(f'git --no-pager show')
    r(f'sleep 3')
    r(f'git push')
    r(f'fedpkg build --target=f33-python || :')
    r(f'koji regen-repo f33-python  || :')
    r(f'while ! /usr/bin/koji wait-repo f33-python --build='
      f'$(rpm --define \'_sourcedir .\'  --define \'fedora 33\' -q '
      f'--qf "%{{NAME}}-%{{VERSION}}-'
      f'%{{RELEASE}}\\n" --specfile {pkg}.spec | head -n1); '
      f'do sleep 15; done | tee -a ../../wait-times')
    r(f'cd ..')
    r(f'rm -rf {pkg}')
    r(f'')
