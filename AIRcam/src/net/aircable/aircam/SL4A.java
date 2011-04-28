/*
 * Copyright (C) 2010 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package net.aircable.aircam;

import com.googlecode.android_scripting.AndroidProxy;
import java.net.Socket;
import java.net.UnknownHostException;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.OutputStreamWriter;
import java.io.BufferedOutputStream;
import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONException;

/**
 * @author Naranjo Manuel Francisco <manuel@aircable.net>
 */
public class SL4A {
    private AndroidProxy proxy;

    private String host;
    private int port;
    private String secret;

    private Socket connection;
    private BufferedReader input;
    private PrintWriter output;
    
    private int id = 0;

    public void connect() throws UnknownHostException, IOException, JSONException{
		proxy = AndroidProxy.sProxy;
		host = proxy.getAddress().getHostName();
		port = proxy.getAddress().getPort();
		secret = proxy.getSecret();
		
		connection = new Socket(host, port);
		input = new BufferedReader(new InputStreamReader(
					connection.getInputStream(), "8859_1"),
		                                      1 << 13);
		output = new PrintWriter(new OutputStreamWriter( new BufferedOutputStream(
							connection.getOutputStream(), 1 << 13),
		                                "8859_1"), true);
		id = 0;
		if (this.secret!=null)
			try {
				this.callMethod("_authenticate", new JSONArray('['+this.secret+']'));
			} catch (RuntimeException e) {
				if (!e.getMessage().contains("Unknown RPC"))
					throw e;
			}
	}
    
    public JSONObject callMethod(String method) 
    	throws JSONException, RuntimeException, IOException{
    	return this.callMethod(method, "");
    }
    
    public JSONObject callMethod(String method, Object[] params) 
    		throws JSONException, RuntimeException, IOException{
    	String temp = "";
    	for (Object i: params)
    		temp+=i.toString()+",";
    	return this.callMethod(method, new JSONArray(temp));
    }
    
    public JSONObject callMethod(String method, String params) 
    		throws JSONException, RuntimeException, IOException{
    	return this.callMethod(method, new JSONArray('[' + params + ']'));
    }

    public JSONObject callMethod(String method, JSONArray params) 
    		throws JSONException, RuntimeException, IOException{
		String response;
		JSONObject request, out;
	
		if (this.connection==null)
			throw new RuntimeException("No connection");
		
		request = new JSONObject();
		request.put("id", this.id);
		request.put("method", method);
		request.put("params", params);
		
		this.id += 1;
	
		this.output.write(request.toString() + '\n');
		this.output.flush();
	
		response = this.input.readLine();
	
		if (response==null){
			this.connection.close();
			this.connection = null;
			this.input.close();
			this.input = null;
			this.output.close();
			this.output = null;			
			throw new RuntimeException("lost connection");
		}
		out = new JSONObject(response);
		if (out.has("error")){
			@SuppressWarnings("unused")
			Object a = out.get("error");
		    if (out.get("error") != JSONObject.NULL)
		    	throw new RuntimeException(out.getString("error"));
		}
		return out;
    }
}
