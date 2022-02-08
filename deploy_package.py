# -*- coding: utf-8 -*-
# Israel García >>> ibgg11@gmail.com

import os
import sys
import shutil
from datetime import datetime

#python .\deploy_order.py --sorgname att_dev --dorgname att_uat --sbrname prepago --dbrname fulluat --package ./manifest/package.xml --outputdir ./manifest --order_name PRE_Sprint_4_PI6-Prepago_1 --testslist test1 --backupdir C:\Users\israel.garcia\Documents\tmp2

params_list = ['--sbrname', '--sorgname', '--dorgname', '--package', '--dbrname', '--outputdir', '--order_name', '--testslist', '--backupdir']
params = {}
timestamp = datetime.now().strftime("%m-%d-%Y%H%M%S") 

print('SF ORDERS DEPLOYER'.center(100, ':'))

#Read params from comandline
def read_params():
    for index, param in enumerate(sys.argv):
        if param in params_list:
            params[param] = sys.argv[index+1]
    print('\n'+'Lets deploy order {order_name} from {sorgname} to {dorgname}'.format(order_name=params['--order_name'],sorgname=params['--sorgname'],dorgname=params['--dorgname']).center(100, '.')+'\n')
    print(params)

    backup_folder = '{backupdir}\\{order_name}'.format(backupdir=params['--backupdir'], order_name=params['--order_name'])
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder, mode=0o777)

    backupfile = backup_folder+'\\report.txt'
    input_command = 'python '+' '.join(sys.argv)
    os.system('echo [COMMAND] > {backupfile}'.format(backupfile=backupfile))
    os.system('echo {deployment} >> {backupfile}'.format(deployment=input_command, backupfile=backupfile))

#Lets remove old packages
def clean_data():
    print('\n'+'Lets delete old packages'.center(100, '.')+'\n')
    
    spackage = '{outputdir}/origin/unpackaged.zip'.format(outputdir=params['--outputdir'])
    if os.path.exists(spackage):
        os.remove(spackage)
        print('\n'+'Removed package {spackage}'.format(spackage=spackage))
    else:
        print('\n'+'Nothig to clean in {spackage}!!'.format(spackage=spackage))
    
#SFDX mdapi package validation    
def validate_package():
    print('\n'+'Lets validate the package in destination org {dorgname}'.format(dorgname=params['--dorgname']).center(100, '.')+'\n')

    if not os.path.exists(params['--package']):
        print('{package} does not exist!!'.format(package=params['--package']))
        exit()
    os.system('sfdx force:mdapi:retrieve -u {sorgname} -k {package} -r {outputdir}/origin'.format(sorgname=params['--sorgname'], package=params['--package'], outputdir=params['--outputdir']))
    
    if not os.path.exists('.\logs'):
        os.makedirs('.\logs', mode=0o777)
    
    if ('--testslist' in params):
        os.system('sfdx force:mdapi:deploy -c -f {outputdir}\origin\unpackaged.zip -w 10 -u {dorgname} -l RunSpecifiedTests -r {testslist} > validation-{timestamp}.log'.format(outputdir=params['--outputdir'], dorgname=params['--dorgname'], testslist=params['--testslist'], timestamp=timestamp))
    else:
        os.system('sfdx force:mdapi:deploy -c -f {outputdir}\origin\unpackaged.zip -w 10 -u {dorgname} -l NoTestRun > validation-{timestamp}.log'.format(outputdir=params['--outputdir'], dorgname=params['--dorgname'], timestamp=timestamp))    
    os.rename('validation-{timestamp}.log'.format(timestamp=timestamp), './logs/validation-{timestamp}.log'.format(timestamp=timestamp))
    
    with open('./logs/validation-{timestamp}.log'.format(timestamp=timestamp), 'r') as f:
        last_line = f.readlines()
        for line in last_line:
            if 'ERROR ' in line.upper():
                print('...Invalid package, check validation log for details!!!')
                exit()
        print ('...Valid package!!!')

    shutil.copyfile(params['--package'], '{backupdir}/{order_name}/package.xml'.format(backupdir=params['--backupdir'], order_name=params['--order_name']))
    
    backupfile = '{backupdir}\\{order_name}\\report.txt'.format(backupdir=params['--backupdir'], order_name=params['--order_name'])
    os.system('echo [ORGANIZATION SOURCE] {sorgname} >> {backupfile}'.format(sorgname = params['--sorgname'],backupfile=backupfile))
    os.system('echo [ORGANIZATION TARGET] {dorgname} >> {backupfile}'.format(dorgname = params['--dorgname'],backupfile=backupfile))

#Lets backup destionation org package in local directory
def backup_dest_metadata():
    print('\n'+'Lets backup destination org {dorgname} metadata in {backupdir}/{order_name}/dest'.format(dorgname=params['--dorgname'], backupdir=params['--backupdir'], order_name=params['--order_name']).center(100, '.')+'\n')
    os.system('sfdx force:mdapi:retrieve -u {dorgname} -k {package} -r {backupdir}/{order_name}/dest'.format(dorgname=params['--dorgname'], package=params['--package'], backupdir=params['--backupdir'], order_name=params['--order_name']))

#Lets backup source org package in local directory
def backup_origin_metadata():
    print('\n'+'Lets backup origin org {sorgname} metadata in {backupdir}/{order_name}/origin'.format(sorgname=params['--sorgname'], backupdir=params['--backupdir'], order_name=params['--order_name']).center(100, '.')+'\n')
    os.system('sfdx force:mdapi:retrieve -u {sorgname} -k {package} -r {backupdir}/{order_name}/origin'.format(sorgname=params['--dorgname'], package=params['--package'], backupdir=params['--backupdir'], order_name=params['--order_name']))

#Lets retrieve data defined in package.xml from target org and push to target branch before deployment
def backup_dest_repo():
    print('\n'+'Lets backup in destination branch {dbranch}'.format(dbranch=params['--dbrname']).center(100, '.')+'\n')
    os.system('git checkout {dbrname}'.format(dbrname=params['--dbrname']))
    os.system('git pull')
    os.system('git commit -m \"backup {commit_message}\"'.format(commit_message=datetime.now().strftime("%m-%d-%Y, %H:%M:%S")))
    os.system('sfdx force:source:retrieve -u {dorgname} -x {package}'.format(dorgname=params['--dorgname'], package=params['--package']))
    os.system('git add .')
    os.system('git commit -m \"deployment backup... {date_backup}\"'.format(date_backup=datetime.now().strftime("%m-%d-%Y, %H:%M:%S")))
    os.system('git push')

    backupfile = '{backupdir}\\{order_name}\\report.txt'.format(backupdir=params['--backupdir'], order_name=params['--order_name'])
    os.system('echo [TARGET BRANCH NAME] >> {backup_file}'.format(backup_file=backupfile))
    os.system('git rev-parse --abbrev-ref HEAD >> {backup_file}'.format(backup_file=backupfile))

    os.system('echo [BACKUP COMMIT ID] >> {backup_file}'.format(backup_file=backupfile))
    os.system('git rev-parse HEAD >> {backup_file}'.format(backup_file=backupfile))
    
#Lets versioning into 
def backup_origin_repo():
    print('\n'+'Lets backup in source branch {sbrname}'.format(sbrname=params['--sbrname']).center(100, '.')+'\n')
    os.system('git checkout {sbrname}'.format(sbrname=params['--sbrname']))
    os.system('git pull')
    os.system('git add .')
    os.system('git commit -m "deployment backup {commit_message}"'.format(commit_message=datetime.now().strftime("%m-%d-%Y, %H:%M:%S")))
    os.system('git checkout -b {order_name}'.format(order_name=params['--order_name']))
    os.system('sfdx force:source:retrieve -u {sorgname} -x {package}'.format(sorgname=params['--sorgname'], package=params['--package']))
    os.system('git add .')
    os.system('git commit -m "deployment for new metadata ... {commit_message}"'.format(commit_message=datetime.now().strftime("%m-%d-%Y, %H:%M:%S")))
   
def deploy_package():
    print('\n'+'Lets deploy package in {dorgname}'.format(dorgname=params['--dorgname']).center(100, '.')+'\n')
#    os.system('sfdx force:mdapi:deploy -f {outputdir}\origin\unpackaged.zip -w 10 -u {dorgname} -l NoTestRun > validation-{timestamp}.log'.format(outputdir=params['--outputdir'], dorgname=params['--dorgname'], timestamp=timestamp))
    if ('--testslist' in params):
        os.system('sfdx force:mdapi:deploy -f {outputdir}\origin\unpackaged.zip -w 10 -u {dorgname} -l RunSpecifiedTests -r {testslist} > validation-{timestamp}.log'.format(outputdir=params['--outputdir'], dorgname=params['--dorgname'], testslist=params['--testslist'], timestamp=timestamp))
    else:
        os.system('sfdx force:mdapi:deploy -f {outputdir}\origin\unpackaged.zip -w 10 -u {dorgname} -l NoTestRun > validation-{timestamp}.log'.format(outputdir=params['--outputdir'], dorgname=params['--dorgname'], timestamp=timestamp))    

    os.system('git checkout {sbrname}'.format(sbrname=params['--sbrname']))
    os.system('git merge {order_name}'.format(order_name=params['--order_name']))
    os.system('git push')

    backupfile = '{backupdir}\\{order_name}\\report.txt'.format(backupdir=params['--backupdir'], order_name=params['--order_name'])
    os.system('echo [DEPLOYMENT ID] >> {backup_file}'.format(backup_file=backupfile))
    os.system('sfdx force:mdapi:deploy:report -u {dorgname} >> {backup_file}'.format(dorgname=params['--dorgname'], backup_file=backupfile))

def compare_sources():
    os.system('sfdx force:source:retrieve -u {dorgname} -x {package}'.format(dorgname=params['--dorgname'], package=params['--package']))
    os.system('git diff')
    os.system('ls *.orig')

if __name__ == "__main__":
    read_params()               # Read command line params
    clean_data()                # Clean old deployed packages
    validate_package()          # Validate package
    backup_dest_metadata()      # Backup destination org metadata in local directory before deployment
    backup_origin_metadata()    # Backup source org metadata in local directory before deployment
    backup_dest_repo()          # Backup destination metadata in git branch
    backup_origin_repo()        # Backup source org metadata in git branch
    deploy_package()            # Deploy package
