Name: offlineimap
Summary: Powerful IMAP/Maildir synchronization and reader support
Version: 4.0.13
Release: 1
License: GPL
Group: Applications/Internet
URL: http://quux.org:70/devel/offlineimap
Source0: %{name}_%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Requires: python >= 2.2.1

%description
OfflineIMAP is  a  tool  to   simplify   your   e-mail  reading.   With
OfflineIMAP,  you  can  read  the same mailbox from multiple computers.
You get a current copy of your messages on each computer,  and  changes
you make one place will be visible on all other systems.  For instance,
you can delete a message on your home  computer,  and  it  will  appear
deleted  on  your work computer as well.  OfflineIMAP is also useful if
you want to use a mail reader that does not have IMAP support, has poor
IMAP support, or does not provide disconnected operation.

%prep
%setup

%build
python setup.py build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --root=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc docs manual.* README COPY* ChangeLog* UPGRADING
/usr/bin/*
/usr/lib/python*

%changelog
* Sun May 14 2006 Adam Spiers <adam@spiers.net> 4.0.13-1
- Updated for 4.0.13

* Sat Apr 29 2006 Adam Spiers <offlineimap@adamspiers.org> 4.0.11-2
- Add patch for Groupwise IMAP servers.

* Fri Apr 28 2006 Adam Spiers <offlineimap@adamspiers.org> 4.0.11-1
- Initial build.


