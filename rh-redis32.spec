%{!?scl_vendor: %global scl_vendor rh}
%global scl_name_base    redis
%global scl_name_version 32
%global scl              %{scl_vendor}-%{scl_name_base}%{scl_name_version}
%global macrosdir        %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_root_sysconfdir}/rpm; echo $d)
%global install_scl      1
%global nfsmountable     1

%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary:       Package that installs Redis 3.2
Name:          %scl_name
Version:       2.3
Release:       1%{?dist}
Group:         Development/Languages
License:       GPLv2+

Source0:       macros-build
Source1:       README
Source2:       LICENSE
Source3:       register
Source4:       deregister
Source5:       50-copy-files
Source6:       50-clean-files

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: scl-utils-build
BuildRequires: help2man
# Temporary work-around
BuildRequires: iso-codes

Requires:      %{?scl_prefix}redis%{?_isa}
Requires:      %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description
This is the main package for %scl Software Collection,
that install Redis and Sentinel servers.


%package runtime
Summary:   Package that handles %scl Software Collection.
Group:     Development/Languages
Requires:  scl-utils
Requires(post): policycoreutils-python libselinux-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.


%package build
Summary:   Package shipping basic build configuration
Group:     Development/Languages
Requires:  scl-utils-build
Requires:  %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description build
Package shipping essential configuration macros
to build %scl Software Collection.


%package scldevel
Summary:   Package shipping development files for %scl
Group:     Development/Languages
Requires:  %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.


%prep
%setup -c -T

cat <<EOF | tee enable
export PATH=%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
EOF

# generate rpm macros file for depended collections
cat << EOF | tee scldev
%%scl_%{scl_name_base}         %{scl}
%%scl_prefix_%{scl_name_base}  %{scl_prefix}
EOF

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE1})}
EOF

# copy additional files
cp %{SOURCE2} %{SOURCE3} %{SOURCE4} %{SOURCE5} %{SOURCE6} .


%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7
# Fix single quotes in man page. See RHBZ#1219527
#
# http://lists.gnu.org/archive/html/groff/2008-06/msg00001.html suggests that
# using "'" for quotes is correct, but the current implementation of man in 6
# mangles it when rendering.
sed -i "s/'/\\\\(aq/g" %{scl_name}.7
 

%install
install -D -m 644 enable         %{buildroot}%{_scl_scripts}/enable
install -D -m 644 register       %{buildroot}%{_scl_scripts}/register
install -d -m 755                %{buildroot}%{_scl_scripts}/register.content
install -D -m 644 50-copy-files  %{buildroot}%{_scl_scripts}/register.d/50-copy-files
install -D -m 644 deregister     %{buildroot}%{_scl_scripts}/deregister
install -D -m 644 50-clean-files %{buildroot}%{_scl_scripts}/deregister.d/50-clean-files
sed -e 's:@SCLDIR@:%{_scl_scripts}:' \
    -i %{buildroot}%{_scl_scripts}/*gister

install -D -m 644 scldev %{buildroot}%{macrosdir}/macros.%{scl_name_base}-scldevel
install -D -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

install -d -m 755 %{buildroot}%{_datadir}/licenses

%scl_install

# Add the scl_package_override macro
sed -e 's/@SCL@/%{scl_name_base}%{scl_name_version}/g' \
    -e 's/@VENDOR@/%{scl_vendor}/' \
    %{SOURCE0} \
  | tee -a %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config

# Move in correct location, if needed
if [ "%{_root_sysconfdir}/rpm" != "%{macrosdir}" ]; then
  mv  %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config \
      %{buildroot}%{macrosdir}/macros.%{scl}-config
fi


%post runtime
# Simple copy of context from system root to SCL root.
semanage fcontext -a -e /                      %{?_scl_root}     &>/dev/null || :
semanage fcontext -a -e %{_root_sysconfdir}    %{_sysconfdir}    &>/dev/null || :
semanage fcontext -a -e %{_root_localstatedir} %{_localstatedir} &>/dev/null || :
selinuxenabled && load_policy || :
restorecon -R %{?_scl_root}     &>/dev/null || :
restorecon -R %{_sysconfdir}    &>/dev/null || :
restorecon -R %{_localstatedir} &>/dev/null || :


%files


%{!?_licensedir:%global license %%doc}

%if 0%{?fedora} < 19 && 0%{?rhel} < 7
%files runtime
%else
%files runtime -f filesystem
%endif
%defattr(-,root,root)
%license LICENSE
%doc README
%scl_files
%{_scl_scripts}/register
%{_scl_scripts}/register.d/
%{_scl_scripts}/register.content/
%{_scl_scripts}/deregister
%{_scl_scripts}/deregister.d/
%{?_licensedir:%{_datadir}/licenses}


%files build
%defattr(-,root,root)
%{macrosdir}/macros.%{scl}-config


%files scldevel
%defattr(-,root,root)
%{macrosdir}/macros.%{scl_name_base}-scldevel


%changelog
* Wed Jul 27 2016 Remi Collet <rcollet@redhat.com> 2.3-1
- initial package for rh-redis32 in RHSCL-2.3

