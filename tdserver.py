# -*- coding: utf-8 -*-
import cookielib
import urllib
import urllib2
import ssl


##POST /tdserver/Device%20Admin/querydevice.jsp?tempFlag=1&migrateFlag=0 HTTP/1.1\r\n
##HWID=6c71d940ab32&ownerName=&tempFlag=1&ownerID=&startDate=&endDate=&startBirthDate=&endBirthDate=&stolenFlag=

##http://tdserver/tdserver/Device%20Admin/fetch_key_deal.jsp?HWID=6C71D9457BC9&bootTick=3&Submit=Aceptar

class TDServer(object):
	def __init__(self, user, passwd):
		self.username = user
		self.password = passwd
		self.cj = cookielib.CookieJar()
		#gcontext = ssl._create_unverified_context()
		self.opener = urllib2.build_opener(
			urllib2.HTTPRedirectHandler(),
			urllib2.HTTPHandler(debuglevel=0),
			urllib2.HTTPSHandler(debuglevel=0),
			urllib2.HTTPCookieProcessor(self.cj),
		)
		self.opener.addheaders = [
			('User-agent', ('Mozilla/4.0 (compatible; MSIE 6.0; '
			'Windows NT 5.2; .NET CLR 1.1.4322)'))
		]

	def doLogin(self):
		"""
		Handle login. This should populate our cookie jar.
		"""
		login_data = urllib.urlencode({
			'operatorName' : self.username,
			'password' : self.password,
			'submit' : 'Iniciar+sesi%C3%B3n',
		})

		response = self.opener.open("http://172.16.0.2/tdserver/login_deal.jsp", login_data)		### deberia devolver verdadero o falso segun se logueo o no

	def getStatus(self, hwid):
		"""
		Busca los datos de una netbook con el HWID dado. El HWID debe ser valido.
		Devuelve un diccionario con los datos de la net
		"""
		# need this twice - once to set cookies, once to log in...


		# busca en el servidor si esta robada
		try:
			self.doLogin()
			self.doLogin()
			status={'hwid': hwid, 'ownerid': '', 'deviceid': '', 'stolenflag': 0, 'comment': '', 'expDate': '', 'lastBT': -1}

			response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/modify_device.jsp?HWID="+hwid.upper())
			response_str = ''.join(response.readlines())
			i = response_str.find('name=ownerID')
			j = response_str.find('value="', i)
			status["ownerid"] = response_str[j+7:response_str.find('"', j+7)]

			i = response_str.find('name=ownerName')
			j = response_str.find('value="', i)
			status["deviceid"] = response_str[j+7:response_str.find('"', j+7)]

			i = response_str.find('<INPUT class="radio" name="stolenFlag" value=0 type=radio CHECKED>')
			if i != -1:
				status["stolenflag"] = 0
			else:
				status["stolenflag"] = 1

			i = response_str.find('name="deviceComment"')
			j = response_str.find('">', i)
			status["comment"] = response_str[j+2: response_str.find('</', j+1)]


			# busca el resto de los datos en otra pestania
			data = urllib.urlencode({
				'HWID' : hwid.upper(),
				'tempFlag': 1,
				'ownerName': '',
				'isQuery': 1
			})
			response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/fetch_key.jsp", data)
			response_str = ''.join(response.readlines())

			# la primera vez que lo encontramos tiene el HWID
			whatToFind='<td class="result1" align="center" valign="middle">'
			pos = response_str.find(whatToFind)

			# la segunda vez que lo encontramos tiene el fecha de expiracion
			pos = response_str.find(whatToFind, pos + 1)
			status['expDate']=response_str[pos+len(whatToFind):response_str.find("</td>",pos)]
			# la tercera vez que lo encontramos tiene el ultimo bt informado
			pos = response_str.find(whatToFind, pos + 1)
			status['lastBT']=response_str[pos+len(whatToFind):response_str.find("</td>",pos)]
			# la cuarta vez que lo encontramos tiene la cantidad de arranques que se le dio
			# la quinta vez que lo encontramos tiene una cadena con el estado de provision
			return {'error': None, 'status': status}
		except urllib2.URLError, e:
			return {'error': str(e), 'status': None}



	def getCode(self, hwid, bt):
		# need this twice - once to set cookies, once to log in...
		try:
			self.doLogin()
			self.doLogin()
			data = urllib.urlencode({
				'HWID' : hwid,
				'bootTick' : bt,
				'Submit' : 'Aceptar',
			})
			response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/fetch_key_deal.jsp", data)
			response_str = ''.join(response.readlines())
			mstr = '<td align="center" valign="middle"><font style="font-weight:bold; color:#404BBA; font-size:24px">'
			index = response_str.find(mstr)
			code = '';
			if index != -1:
				index = index + len(mstr)
				code = response_str[index:index+10]
				return {'error': None, 'code': code}
			return {'error': 'Error: ???', 'code': None}
		except urllib2.URLError, e:
			return {'error': e, 'code': None}


	def addNetbook(self, hwid, studentID, deviceID, comment=""):
		"""
		Agrega una netbook
		"""
		# borra la netbook si está aceptada
		data = urllib.urlencode({
			'page2': 'null',
			'HWID': hwid,
			'ownerID': studentID.upper(),
			'ownerName': deviceID.upper(),
			'bootTick': '0',
			'specialFlag': '0',
			'stolenFlag': '0',
			'deviceComment': comment,
			'page2': '3'
		})
		response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/add_pc_deal.jsp", data)
		#response_str = ''.join(response.readlines())
		#POST /tdserver/Device%20Admin/add_pc_deal.jsp
		#
		# deberia devolver verdadero o falso segun se haya agregado


	### FUNCIONA!!! Probada 30/11/15
	def searchByHWID(self, hwid):
		"""
		Permite buscar netbooks por HWID
		\param: hwid	hwid o porcion del mismo de la netbook que se desea buscar
		\return:		lista de hwid's validos que coinciden con la cadena
		"""
		matches = []
		data = urllib.urlencode({
			'HWID' : hwid,
		})
		response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/querydevice.jsp", data)
		response_str = ''.join(response.readlines())
		i = response_str.find('modify_device.jsp?HWID=')
		while i != -1:
			newHWID = response_str[i+23: i+35]
			matches.append(newHWID)
			i = response_str.find('modify_device.jsp?HWID=', i + 1)
		return matches

	### Busca por el campo IDDispositivo
	### FUNCIONA!!! Probada 30/11/15
	def searchByDevID(self, devId):
		matches = []
		data = urllib.urlencode({
			'ownerName' : devId,
		})
		response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/querydevice.jsp", data)
		response_str = ''.join(response.readlines())
		i = response_str.find('modify_device.jsp?HWID=')
		while i != -1:
			newHWID = response_str[i+23: i+35]
			matches.append(newHWID)
			i = response_str.find('modify_device.jsp?HWID=', i + 1)
		return matches

	### Busca por el campo Nombre de Alumno
	### FUNCIONA!!! Probada 30/11/15
	def searchByOwnerName(self, ownerID):
		matches = []
		data = urllib.urlencode({
			'ownerID' : ownerID,
		})
		response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/querydevice.jsp", data)
		response_str = ''.join(response.readlines())
		i = response_str.find('modify_device.jsp?HWID=')
		while i != -1:
			newHWID = response_str[i+23: i+35]
			matches.append(newHWID)
			i = response_str.find('modify_device.jsp?HWID=', i + 1)
		return matches

	### Funcion auxiliar para volcar respuestas
	def dumpLastResponse(self, response):
		out=open('last_response.txt', 'w')
		out.write(response)
		out.close()


	def deleteNetbook(self, hwid):
		"""
		Borra o rechaza la netbook en caso de que exista
		"""
		# borra la netbook si está aceptada
		data = urllib.urlencode({
			'id' : ','+hwid,
		})
		response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/delete_pc_deal.jsp", data)
		#response_str = ''.join(response.readlines())

		# si está como dispositivo temporal, la rechaza
		data = urllib.urlencode({
			'Submit': 'Sí',
			'id' : ','+hwid,
		})
		response = self.opener.open("http://172.16.0.2/tdserver/Device%20Admin/reject_temp_pc_deal.jsp", data)
		#response_str = ''.join(response.readlines())

if __name__ == '__main__':
	username = 'admin'
	password = 'pass'
	server = TDServer(username, password)
	server.doLogin()

	hwid = str(raw_input("Ingrese el HWID (sin guiones ni espacios): "))
	hwid = hwid.upper()
	
	outputFile = open("C:\\"+hwid+".txt", "w")

	for boottick in range(1, 50):
		hex_boottick = hex(boottick).split('x')[-1].upper()
		print "%s: Pidiendo codigo para BT: %s"%(hwid,hex_boottick)  
		code = server.getCode(hwid, hex_boottick)
			
		outputFile.write("%i: %s\n"%(hex_boottick, code))		

	outputFile.close()

	#print server.getStatus("6C71D94097CD")
	#print server.getStatus("DC85DE6661E7")
	#print server.getStatus("6C71D93E7F6F")




# Se puede buscar por nombre y por ID
#http://tdserver/tdserver/Device%20Admin/querydevice.jsp?tempFlag=1&migrateFlag=0&ownerName=Lopez

#http://tdserver/tdserver/Device%20Admin/reject_temp_pc.jsp?id=,20689D75DC2C
