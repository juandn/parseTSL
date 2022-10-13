import sys, os, subprocess

import xml.etree.ElementTree as ET
import lxml.etree

import unicodedata
import re

ns = {'d': 'http://uri.etsi.org/02231/v2#', 'xml' : 'http://www.w3.org/XML/1998/namespace', "re": "http://exslt.org/regular-expressions"}
root = lxml.etree.parse('TSL.xml')

###
### usefull functions
###

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

###
### check functions
###

def is_granted(element):
  xpath_string = "d:ServiceStatus[text()='http://uri.etsi.org/TrstSvc/TrustedList/Svcstatus/granted']"
  granted_services = element.xpath(xpath_string,namespaces=ns)
  if len(granted_services) != 0:
    return True
  else:
    return False

def is_CA_QT(element):
  xpath_string = "d:ServiceTypeIdentifier[text()='http://uri.etsi.org/TrstSvc/Svctype/CA/QC']"
  if len(element.xpath(xpath_string,namespaces=ns)) != 0:
    return True
  else:
    return False

def is_ForeSignature(element):
  xpath_string = "d:ServiceInformationExtensions/d:Extension/d:AdditionalServiceInformation/d:URI[text()='http://uri.etsi.org/TrstSvc/TrustedList/SvcInfoExt/ForeSignatures']"
  if len(element.xpath(xpath_string,namespaces=ns)) != 0:
    return True
  else:
    return False

###
### commands functions
###

def search_provider(provider):
  xpath_string = '//d:TSPTradeName/d:Name[text()[re:match(.,"'+ provider +'","i")]]/ancestor::d:TrustServiceProvider/descendant::d:ServiceInformation'
  resultados = root.xpath(xpath_string,namespaces=ns)
  print(f'Found: {len(resultados)} providers')
  for element in resultados:
    if is_granted(element) and is_CA_QT(element) and is_ForeSignature(element):
      print_cert(element)

def search_service(service):
  xpath_string = '//d:ServiceName/d:Name[text()[re:match(.,"'+ service +'","i")]]/ancestor::d:ServiceInformation'
  resultados = root.xpath(xpath_string,namespaces=ns)
  print(resultados)
  for element in resultados:
    if is_granted(element) and is_CA_QT(element) and is_ForeSignature(element):
      print_cert(element)

def list_services():
  service_names = get_services()
  for name in service_names:
    print(name)

  print(f'\nTotal services found: {len(service_names)}')

def list_providers():
  providers_names = get_providers()
  for name in providers_names:
    print(name)

  print(f'\nTotal providers found: {len(providers_names)}')

def export(format_type, param):
  if format_type == 'dir':
    export_as_dir(param)
  elif format_type == 'file':
    export_as_file(param)
  elif format_type == 'keystore':
    export_as_keystore(param)
  else:
    print(f'Format type no supported.')



###
### print functions
###

def print_cert(ServiceInformation):
  ServiceTypeIdentifier = ServiceInformation.xpath('d:ServiceTypeIdentifier',namespaces=ns)[0].text

  X509Certificate = ServiceInformation.xpath('d:ServiceDigitalIdentity/d:DigitalId/d:X509Certificate',namespaces=ns)
  X509Certificate_text=''
  if len(X509Certificate) > 0:
    X509Certificate_text = X509Certificate[0].text

  ServiceName = ServiceInformation.xpath('d:ServiceName/d:Name',namespaces=ns)
  ServiceName_text=''
  if len(ServiceName) > 0:
    ServiceName_text = ServiceName = ServiceName[0].text

  print("########################################")
  print("ServiceTypeIdentifier: " + ServiceTypeIdentifier)
  print("ServiceName: " + ServiceName_text)
  print("-----BEGIN CERTIFICATE-----\n" + X509Certificate_text + "\n-----END CERTIFICATE-----\n\n")

def print_services_info(filter_str):
  services_info = get_services_info(filter_str)
  count =0

  for TSProvider, services in services_info.items():
    for service_info in services:
      count += 1
      print("########################################")
      print("ServiceTypeIdentifier: " + service_info['ServiceTypeIdentifier'])
      print("ServiceName: " + service_info['name'])
      print("-----BEGIN CERTIFICATE-----\n" + service_info['X509Certificate'] + "\n-----END CERTIFICATE-----\n\n")
  print(f"Total services displayed: {count}")

def print_tree():
  services_info = get_services_info('')
  count =0

  for TSProvider, services in services_info.items():
    print(f'{TSProvider}')
    for service_info in services:
       print(f"\t{service_info['name']}")

###
### getters
###

def get_services_info(filter_str):
  services_info = {}

  xpath_string = "//d:TrustServiceProvider"
  for TrustServiceProvider in root.xpath(xpath_string, namespaces=ns):
    TrustServiceProvider_name = TrustServiceProvider.xpath('d:TSPInformation/d:TSPTradeName/d:Name[1]/text()',namespaces=ns)[0]
    if TrustServiceProvider_name.startswith('VATES-'):
      TrustServiceProvider_name = TrustServiceProvider.xpath('d:TSPInformation/d:TSPTradeName/d:Name[2]/text()',namespaces=ns)[0]
    if TrustServiceProvider_name == filter_str or filter_str == '':
      services = []
      for ServiceInformation in TrustServiceProvider.xpath("d:TSPServices/d:TSPService/d:ServiceInformation", namespaces=ns):
        if is_granted(ServiceInformation) and is_CA_QT(ServiceInformation) and is_ForeSignature(ServiceInformation):
          service_info = {}
          service_info['name'] = ServiceInformation.xpath('d:ServiceName/d:Name[1]/text()',namespaces=ns)[0]
          service_info['ServiceTypeIdentifier'] = ServiceInformation.xpath('d:ServiceTypeIdentifier',namespaces=ns)[0].text
          service_info['X509Certificate'] = ServiceInformation.xpath('d:ServiceDigitalIdentity/d:DigitalId/d:X509Certificate',namespaces=ns)[0].text
          services.append(service_info)
      if len(services) >0:
        services_info[TrustServiceProvider_name] = services

  return services_info

def get_services():
  service_names = []

  xpath_string = "//d:TrustServiceProvider"
  for TrustServiceProvider in root.xpath(xpath_string, namespaces=ns):
    for ServiceInformation in TrustServiceProvider.xpath("d:TSPServices/d:TSPService/d:ServiceInformation", namespaces=ns):
      if is_granted(ServiceInformation) and is_CA_QT(ServiceInformation) and is_ForeSignature(ServiceInformation):
        service_names += ServiceInformation.xpath('d:ServiceName/d:Name[1]/text()',namespaces=ns)


  service_names.sort()
  return service_names



def get_providers():
  providers_names = []

  xpath_string = "//d:TrustServiceProvider"
  for TrustServiceProvider in root.xpath(xpath_string, namespaces=ns):
    for ServiceInformation in TrustServiceProvider.xpath("d:TSPServices/d:TSPService/d:ServiceInformation", namespaces=ns):
      if is_granted(ServiceInformation) and is_CA_QT(ServiceInformation) and is_ForeSignature(ServiceInformation):
        name = TrustServiceProvider.xpath('d:TSPInformation/d:TSPTradeName/d:Name[1]/text()',namespaces=ns)
        if name[0].startswith('VATES-'):
          name = TrustServiceProvider.xpath('d:TSPInformation/d:TSPTradeName/d:Name[2]/text()',namespaces=ns)
        providers_names += name


  providers_names = list(dict.fromkeys(providers_names))
  providers_names.sort()
  return providers_names


###
### export functions
###

def export_as_file(param):
  services_info = get_services_info('')
  workfile = param
  count = 0

  with open(workfile, 'w', encoding="utf-8") as f:
    for TSProvider, services in services_info.items():
      for service_info in services:
        count += 1
        f.write("########################################\n")
        f.write("ServiceName: " + service_info['name'] + '\n')
        f.write("-----BEGIN CERTIFICATE-----\n" + service_info['X509Certificate'] + "\n-----END CERTIFICATE-----\n\n")
  print(f"Total services exported: {count}")

def export_as_dir(param):
  services_info = get_services_info('')

  isExist = os.path.exists(param)
  if not isExist:
    os.makedirs(param)
  workpath = param
  count = 0


  for TSProvider, services in services_info.items():
    for service_info in services:
      count += 1
      workfile = workpath + '/' + slugify(service_info['name']) + '.crt'
      with open(workfile, 'w', encoding="utf-8") as f:
        f.write("########################################\n")
        f.write("ServiceName: " + service_info['name'] + '\n')
        f.write("-----BEGIN CERTIFICATE-----\n" + service_info['X509Certificate'] + "\n-----END CERTIFICATE-----\n\n")
  print(f"Total services exported: {count}")

def export_as_keystore(param):
  services_info = get_services_info('')
  JKS_file_name = param
  count = 0

  for TSProvider, services in services_info.items():
    for service_info in services:
      count += 1
      #workfile = workpath + '/' + slugify(service_info['name']) + '.crt'
      workfile = 'tmp.pem'
      alias = slugify(service_info['name'])
      print(f'Working with {alias}')
      with open(workfile, 'w', encoding="utf-8") as f:
        f.write("########################################\n")
        f.write("ServiceName: " + service_info['name'] + '\n')
        f.write("-----BEGIN CERTIFICATE-----\n" + service_info['X509Certificate'] + "\n-----END CERTIFICATE-----\n\n")
      print(f'... Adding cert with alias: {alias}')
      add_certificate_to_keystore(alias, JKS_file_name)
      os.remove('tmp.pem')
  print(f"Total services exported: {count}")

###
### keystore functions
###

def add_certificate_to_keystore(alias, JKS_file_name):
   try:
     subprocess.call(['keytool', '-import', '-storepass', 'changeit', '-noprompt', '-alias', alias, '-keystore', JKS_file_name, '-file', 'tmp.pem'])
   except FileNotFoundError:
     print(f'Not keytools')


###
### main and help
###

def print_help(argv):
  if argv == 'list':
    print('Suported command:')
    print('\tlist [services|providers]')
  elif argv == 'search':
    print('Suported command:')
    print('\tsearch [services|providers] <search string>')
  elif argv == 'export':
    print('Suported command:')
    print('\texport dir <path to dir>\t# path al directorio, el ultimo directorio puede no existir.' )
    print('\texport file <filename>\t# nombre del archivo.')
    print('\texport keystore <filename>\t# nombre del archivo.')
  else:
    print('Supported commands:')
    print('\tlist [services|providers]')
    print('\tshow')
    print('\tsearch [services|providers] <search string>')
    print('\tsearch [services|providers] <search string>')
    print('\ttree')
    print('\texport dir <path to dir>')
    print('\texport file <filename>')
    print('\texport keystore <filename>')

command = ''
subcommand = ''
subcommand_param = ''

if len(sys.argv) == 2:
  command = sys.argv[1]
elif len(sys.argv) == 3:
  command = sys.argv[1]
  subcommand = sys.argv[2]
elif len(sys.argv) == 4:
  command = sys.argv[1]
  subcommand = sys.argv[2]
  subcommand_param = sys.argv[3]

if command == "list":
  if subcommand == 'services':
    list_services()
  elif subcommand == 'providers':
    list_providers()
  else:
    print('List subcommand not suported.')
    print_help("list")
elif command == "search":
  if subcommand == 'services':
    search_service(subcommand_param)
  elif subcommand == 'providers':
    search_provider(subcommand_param)
  else:
    print('Search subcommand not suported')
    print_help("search")
elif command == 'show':
  print_services_info(subcommand)
elif command == 'tree':
  print_tree()
elif command == 'export':
  export(subcommand, subcommand_param)
else:
  print('Acción no soportada.')
  print_help('')
