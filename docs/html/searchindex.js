Search.setIndex({docnames:["apidoc/modules","apidoc/producer","apidoc/producer.events","apidoc/producer.heartbeats","apidoc/producer.love_csc","apidoc/producer.scriptqueue","apidoc/producer.telemetries","index","modules/how_it_works","modules/introduction","modules/readme_link"],envversion:{"sphinx.domains.c":1,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":1,"sphinx.domains.javascript":1,"sphinx.domains.math":2,"sphinx.domains.python":1,"sphinx.domains.rst":1,"sphinx.domains.std":1,"sphinx.ext.intersphinx":1,sphinx:56},filenames:["apidoc/modules.rst","apidoc/producer.rst","apidoc/producer.events.rst","apidoc/producer.heartbeats.rst","apidoc/producer.love_csc.rst","apidoc/producer.scriptqueue.rst","apidoc/producer.telemetries.rst","index.rst","modules/how_it_works.rst","modules/introduction.rst","modules/readme_link.rst"],objects:{"":{producer:[1,0,0,"-"]},"producer.base_ws_client":{BaseWSClient:[1,1,1,""]},"producer.base_ws_client.BaseWSClient":{handle_message_reception:[1,2,1,""],on_connected:[1,2,1,""],on_start_client:[1,2,1,""],on_websocket_error:[1,2,1,""],on_websocket_receive:[1,2,1,""],path:[1,3,1,""],read_config:[1,2,1,""],send_message:[1,2,1,""],start_heartbeat:[1,2,1,""],start_ws_client:[1,2,1,""]},"producer.events":{client:[2,0,0,"-"],producer:[2,0,0,"-"],test_client:[2,0,0,"-"],test_producer:[2,0,0,"-"]},"producer.events.client":{EventsWSClient:[2,1,1,""],main:[2,4,1,""]},"producer.events.client.EventsWSClient":{make_and_send_response:[2,2,1,""],on_start_client:[2,2,1,""],on_websocket_error:[2,2,1,""],on_websocket_receive:[2,2,1,""],send_message_callback:[2,2,1,""]},"producer.events.producer":{EventsProducer:[2,1,1,""]},"producer.events.producer.EventsProducer":{make_callback:[2,2,1,""],process_message:[2,2,1,""],set_remote_evt_callbacks:[2,2,1,""],setup_callbacks:[2,2,1,""]},"producer.events.test_client":{TestEventsClient:[2,1,1,""]},"producer.events.test_client.TestEventsClient":{test_valid_remote_not_in_config:[2,2,1,""]},"producer.events.test_producer":{TestEventsMessages:[2,1,1,""]},"producer.events.test_producer.TestEventsMessages":{setUp:[2,2,1,""],tearDown:[2,2,1,""],test_produced_message_with_event_arrays:[2,2,1,""],test_produced_message_with_event_scalar:[2,2,1,""],wait_for_stream:[2,2,1,""]},"producer.heartbeats":{client:[3,0,0,"-"],producer:[3,0,0,"-"],test_producer:[3,0,0,"-"]},"producer.heartbeats.client":{CSCHeartbeatsWSClient:[3,1,1,""],main:[3,4,1,""]},"producer.heartbeats.client.CSCHeartbeatsWSClient":{on_start_client:[3,2,1,""],on_websocket_error:[3,2,1,""],send_heartbeat:[3,2,1,""]},"producer.heartbeats.producer":{HeartbeatProducer:[3,1,1,""]},"producer.heartbeats.producer.HeartbeatProducer":{get_heartbeat_message:[3,2,1,""],monitor_remote_heartbeat:[3,2,1,""],start:[3,2,1,""]},"producer.heartbeats.test_producer":{TestHeartbeatsMessages:[3,1,1,""]},"producer.heartbeats.test_producer.TestHeartbeatsMessages":{setUp:[3,2,1,""],tearDown:[3,2,1,""],test_heartbeat_not_received:[3,2,1,""],test_heartbeat_received:[3,2,1,""]},"producer.love_csc":{client:[4,0,0,"-"],csc:[4,0,0,"-"],test_csc:[4,0,0,"-"]},"producer.love_csc.client":{LOVEWSClient:[4,1,1,""],main:[4,4,1,""]},"producer.love_csc.client.LOVEWSClient":{on_connected:[4,2,1,""],on_start_client:[4,2,1,""],on_websocket_error:[4,2,1,""],on_websocket_receive:[4,2,1,""]},"producer.love_csc.csc":{LOVECsc:[4,1,1,""]},"producer.love_csc.csc.LOVECsc":{add_observing_log:[4,2,1,""]},"producer.love_csc.test_csc":{TestLOVECsc:[4,1,1,""],TestWebsocketsClient:[4,1,1,""]},"producer.love_csc.test_csc.TestLOVECsc":{test_add_observing_log:[4,2,1,""]},"producer.love_csc.test_csc.TestWebsocketsClient":{test_csc_client:[4,2,1,""]},"producer.main":{main:[1,4,1,""]},"producer.scriptqueue":{client:[5,0,0,"-"],producer:[5,0,0,"-"]},"producer.scriptqueue.client":{ScriptQueueWSClient:[5,1,1,""],init_client:[5,4,1,""],main:[5,4,1,""]},"producer.scriptqueue.client.ScriptQueueWSClient":{on_start_client:[5,2,1,""],on_websocket_error:[5,2,1,""],on_websocket_receive:[5,2,1,""],send_message_callback:[5,2,1,""]},"producer.scriptqueue.producer":{ScriptQueueProducer:[5,1,1,""]},"producer.scriptqueue.producer.ScriptQueueProducer":{callback_available_scripts:[5,2,1,""],callback_config_schema:[5,2,1,""],callback_queue:[5,2,1,""],callback_queue_script:[5,2,1,""],callback_script_checkpoints:[5,2,1,""],callback_script_description:[5,2,1,""],callback_script_logLevel:[5,2,1,""],callback_script_metadata:[5,2,1,""],callback_script_state:[5,2,1,""],get_heartbeat_message:[5,2,1,""],get_state_message:[5,2,1,""],monitor_scripts_heartbeats:[5,2,1,""],new_empty_script:[5,2,1,""],parse_script:[5,2,1,""],query_script_config:[5,2,1,""],query_script_info:[5,2,1,""],set_callback:[5,2,1,""],setup:[5,2,1,""],setup_script:[5,2,1,""],update:[5,2,1,""]},"producer.telemetries":{client:[6,0,0,"-"],producer:[6,0,0,"-"],test_client:[6,0,0,"-"],test_producer:[6,0,0,"-"]},"producer.telemetries.client":{TelemetriesClient:[6,1,1,""],main:[6,4,1,""]},"producer.telemetries.client.TelemetriesClient":{on_start_client:[6,2,1,""],send_messages_after_timeout:[6,2,1,""]},"producer.telemetries.producer":{TelemetriesProducer:[6,1,1,""]},"producer.telemetries.producer.TelemetriesProducer":{get_remote_tel_values:[6,2,1,""],get_telemetry_message:[6,2,1,""]},"producer.telemetries.test_client":{TestTelemetriesClient:[6,1,1,""]},"producer.telemetries.test_client.TestTelemetriesClient":{maxDiff:[6,3,1,""],test_produced_message_with_telemetry_scalar:[6,2,1,""]},"producer.telemetries.test_producer":{TestTelemetryMessages:[6,1,1,""]},"producer.telemetries.test_producer.TestTelemetryMessages":{setUp:[6,2,1,""],tearDown:[6,2,1,""],test_produced_message_with_telemetry_scalar:[6,2,1,""]},"producer.test_utils":{WSClientTestCase:[1,1,1,""]},"producer.test_utils.WSClientTestCase":{harness:[1,2,1,""]},"producer.utils":{NumpyEncoder:[1,1,1,""],Settings:[1,1,1,""],check_event_stream:[1,4,1,""],check_stream_from_last_message:[1,4,1,""],getDataType:[1,4,1,""],get_all_csc_names_in_message:[1,4,1,""],get_event_stream:[1,4,1,""],get_parameter_from_last_message:[1,4,1,""],get_stream_from_last_message:[1,4,1,""],make_stream_message:[1,4,1,""],onemsg_generator:[1,4,1,""]},"producer.utils.NumpyEncoder":{"default":[1,2,1,""]},"producer.utils.Settings":{config_path:[1,2,1,""],trace_timestamps:[1,2,1,""],ws_host:[1,2,1,""],ws_pass:[1,2,1,""]},producer:{base_ws_client:[1,0,0,"-"],events:[2,0,0,"-"],heartbeats:[3,0,0,"-"],love_csc:[4,0,0,"-"],main:[1,0,0,"-"],scriptqueue:[5,0,0,"-"],telemetries:[6,0,0,"-"],test_utils:[1,0,0,"-"],utils:[1,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","attribute","Python attribute"],"4":["py","function","Python function"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:attribute","4":"py:function"},terms:{"case":[1,2,3,4,6],"class":[1,2,3,4,5,6,8,9],"default":[1,8],"export":1,"final":8,"float":3,"function":[1,8],"int":[2,3],"new":8,"return":[1,2,3,8,9],"static":1,"throw":[1,8],"true":1,"try":1,For:[1,9],The:[1,9],Then:10,These:[0,8],Used:[5,9],about:8,accept:8,accord:[5,8],acknowledg:[8,9],act:10,act_assert:1,adcress:9,add:[4,5],add_observing_log:4,addit:8,address:8,after:[1,2,3,4,5,6],aliv:8,all:[1,5,8],allow:[1,8,9],allow_nan:1,also:[8,9],ani:8,answer:2,apidoc:7,append:5,applic:10,arbitrari:1,arrang:1,assert_:[1,2,3,4,6],assertalmostequ:[1,2,3,4,6],assertdictequ:[1,2,3,4,6],assertequ:[1,2,3,4,6],assertnotalmostequ:[1,2,3,4,6],assertnotequ:[1,2,3,4,6],assertnotregexpmatch:[1,2,3,4,6],assertraisesregexp:[1,2,3,4,6],assertregexpmatch:[1,2,3,4,6],async:[1,2,3,4,5,6],asynchron:1,asynctest:[1,2,3,4,6],attribut:[1,2,3,4,6],available_script:5,availablescript:5,await:2,back:8,base:[1,2,3,4,5,6],base_ws_cli:[0,2,3,4,5,6],basewscli:[1,2,3,4,5,6],bash:10,been:5,befor:[1,2,3,6],between:[2,3,4,5,6,9,10],both:9,build:5,call:[1,5,8],callback:[1,2,3,4,5,6,8],callback_available_script:5,callback_config_schema:5,callback_queu:5,callback_queue_script:5,callback_script_checkpoint:5,callback_script_descript:5,callback_script_loglevel:5,callback_script_metadata:5,callback_script_st:5,can:[1,9,10],categori:[1,2],charg:8,check_circular:1,check_event_stream:1,check_stream_from_last_messag:1,cleanup:1,client:[0,1,8],code:10,come:[2,6],command:[5,9],command_sim:9,commun:8,compat:3,compon:9,compos:10,config:[1,5,8],config_path:1,configur:[2,7,8,10],connect:[1,2,3,4,5,6,8],consecut:[3,8],consist:[8,9],constructor:8,contain:[1,8,9,10],content:[0,7],control:[4,8],convert:[3,8],copi:10,coro:5,coroutin:1,correctli:3,could:1,count:8,counttestcas:[1,2,3,4,6],creat:[2,8,9],create_doc:10,csc:[0,1,2,3,5,6,7],csc_heartbeat:1,csc_list:[1,2,3,6],cscheartbeatswscli:3,ctrl:10,current:[2,5,9],data:[2,5,8,9],datatyp:2,datetim:3,deconstruct:[2,3,6],def:1,defaulttestresult:[1,2,3,4,6],deliv:2,depend:1,detail:8,diagram:8,dict:[3,8],dictionari:[2,3,8],direct:8,directli:4,distinct:9,docsrc:10,doe:[1,5,8,10],domain:[2,3,4,5,6],driver:8,durat:5,each:[2,5,8,9],edit:10,either:8,els:1,encod:1,ensure_ascii:1,environ:[1,8],error:[1,4,8,9],etc:[1,4],event:[0,1,4,5,6,9],event_nam:2,events_callback:2,eventsproduc:2,eventswscli:2,everi:[1,2,4,8],everytim:[1,4,8],evt:5,evt_heartbeat:8,evt_nam:2,evt_observinglog:8,evt_script:5,exampl:[1,2,9],except:1,exec:10,execut:[1,2,3,4,5,6,9],exercis:[2,3,6],exist:[1,5],expect:[5,8],extract:[5,8],failif:[1,2,3,4,6],failifalmostequ:[1,2,3,4,6],failifequ:[1,2,3,4,6],failunless:[1,2,3,4,6],failunlessalmostequ:[1,2,3,4,6],failunlessequ:[1,2,3,4,6],failunlessrais:[1,2,3,4,6],fals:1,field:8,figur:9,file:[1,7,9],filter:9,finish:1,first:[1,4,8],fix:8,fixtur:[2,3,6],folder:[9,10],follow:10,format:[3,5,8],forward:[8,9],found:1,friendli:5,from:[1,2,3,4,5,6,8,9,10],frontend:8,full:1,gener:[1,3,8],get_all_csc_names_in_messag:1,get_event_stream:1,get_events_messag:8,get_heartbeat_messag:[3,5],get_parameter_from_last_messag:1,get_remote_tel_valu:6,get_state_messag:5,get_stream_from_last_messag:1,get_telemetry_messag:[6,8],getdatatyp:1,getter:8,github:10,give:9,given:[1,8],group:[1,5],handl:[1,2,3,4,5,6,8],handle_message_recept:1,har:1,has:[5,8],have:8,heartbeat:[0,1],heartbeatproduc:3,heartbeatss:3,here:10,hook:[2,3,6],hostnam:9,how:7,html:10,http:10,ignor:9,implement:1,incom:8,indent:1,index:[1,5,7,9,10],indic:9,info:[3,5,8],inform:[8,9],inherit:8,init_cli:5,initi:[1,2,3,4,5,6],initial_st:2,input:8,insid:10,instanc:[8,9],instead:10,instruct:10,integr:[9,10],interfac:8,isstandard:5,iter:1,its:[1,5,8],json:[1,8],jsonencod:1,kei:1,kept:[8,9],last:[3,8],latest:[1,8],launch:1,let:1,librari:[8,9],like:1,limit:9,list:[1,5,8],listen:[1,5,8,9],load:[1,8],locat:9,log:[4,8,9],logevent_descript:5,logevent_metadata:5,loglevel:5,loop:[1,2,3,4,6],lost:[3,8],love:[1,2,3,4,5,6],love_csc:[0,1],love_produc:1,lovecsc:4,lovewscli:4,lsst:[4,9,10],lsst_dds_domain:9,made:[1,4],main:[0,2,3,4,5,6],make:8,make_and_send_respons:2,make_callback:2,make_stream_messag:1,manag:[1,2,3,4,5,6,8,9,10],maxdiff:6,maximum:8,messag:[1,2,3,4,5,6,8,9],method:[1,2,3,4,5,6,8],methodnam:[1,2,3,4,6],middlewar:10,mock:1,mock_datetim:3,modul:[0,7,8,9],monitor:8,monitor_remote_heartbeat:3,monitor_scripts_heartbeat:5,more:1,mount:10,msg:1,must:[1,9],name:[1,3,9],necessari:9,need:10,network:9,never:8,new_empty_script:5,next:8,nlost_subsequ:3,none:[1,2,6],now:3,number:[3,8],numpyencod:1,obj:1,object:[1,2,3,5,6,8],observ:[3,4,8,9],obtain:[2,3],on_connect:[1,4],on_messag:8,on_start_cli:[1,2,3,4,5,6],on_websocket_error:[1,2,3,4,5,6],on_websocket_rec:[1,2,4,5],onc:10,one:1,onemsg_gener:1,onli:1,open:8,oper:9,option:1,order:10,outsid:10,overview:7,packag:[0,7],page:[7,8],pair:8,paramet:[1,2,3,9],pars:[5,8],parse_script:5,part:9,pass:[1,8],password:[8,9],path:1,pleas:10,press:10,process_messag:[2,8],produc:0,program:8,project:0,protocol:8,provid:[8,9,10],publish:[8,9],purpos:10,python:[8,9],queri:5,query_script_config:5,query_script_info:5,queue:[5,8],rais:1,read:[1,8,9],read_config:1,readm:7,rebuild:10,receiv:[1,2,3,4],recept:[1,5,9],recommend:10,reconnect:8,refer:8,remot:[2,6,8,9],remote_nam:3,repo:10,report:8,repositori:[9,10],request:[1,5,8],restart:10,run:[1,8],runtest:[1,2,3,4,6],said:9,sal:[1,8,10],salindex:[1,2,3,5,8],salobj:[2,4,5,8,9],salpy_script:5,same:9,save:5,schema:[2,8],script:[5,8],script_logevent_descriptionc:5,script_logevent_metadatac:5,script_logevent_statec:5,script_logevet_st:5,script_path:5,scriptqueu:[0,1,9],scriptqueueproduc:5,scriptqueuest:5,scriptqueuewscli:5,search:7,second:8,section:8,see:[2,10],seen:1,self:[1,3],send:[1,3,5,8,9],send_heartbeat:3,send_messag:[1,2,3,4,5,6],send_message_callback:[2,5],send_messages_after_timeout:6,sent:9,separ:1,serializ:1,serv:1,server:1,set:[1,2,3,5,6,9],set_callback:5,set_remote_evt_callback:2,setup:[2,3,5,6],setup_callback:2,setup_dev:10,setup_script:5,sever:[2,5,6,8],show:8,shown:9,similarli:8,simul:9,sinc:3,singl:1,skipkei:1,sleepdur:6,softwar:9,sort_kei:1,sourc:[1,9,10],specif:[1,8],specifi:[8,9],split:8,src:[1,10],start:[1,3],start_heartbeat:[1,2,3,4,5,6],start_ws_client:[1,2,3,4,5,6],state:[1,5],store:8,str:3,stream:[1,2,5],stream_nam:1,streamsdict:1,string:[1,3],structur:8,subclass:1,submodul:0,subpackag:0,subsequ:3,succe:5,succesfuli:8,success:9,summaryst:2,support:1,take:1,teardown:[2,3,6],telemetri:[0,1,2,4,9],telemetries_ev:2,telemetriescli:6,telemetriesproduc:6,test:[1,2,3,4,6,9],test_add_observing_log:4,test_avail:[0,1],test_client:[0,1],test_csc:[0,1],test_csc_client:4,test_heartbeat_not_receiv:3,test_heartbeat_receiv:3,test_produc:[0,1],test_produced_message_with_event_arrai:2,test_produced_message_with_event_scalar:2,test_produced_message_with_telemetry_scalar:6,test_scripts_heartbeat:[0,1],test_stat:[0,1],test_util:[0,2,4,6],test_valid_remote_not_in_config:2,testcas:[1,2,3,4,6],testeventscli:2,testeventsmessag:2,testheartbeatsmessag:3,testlovecsc:4,testtelemetriescli:6,testtelemetrymessag:6,testwebsocketscli:4,them:[8,9],thi:[1,8,9,10],those:2,three:9,through:[5,8,9],time:[1,2,4,8,9],timeout:8,timestamp:[3,8],tool:10,top:8,topic:8,trace_timestamp:1,tri:[1,2,5],trigger:[5,8],tupl:1,two:[8,9],type:[1,2,3],typeerror:1,understood:9,updat:[5,8],url:8,use:10,used:[3,9],user:4,uses:[8,9],using:[5,9],usr:[1,10],util:0,valu:[1,2,8],variabl:[1,8],via:8,visual:9,wai:10,wait_for_stream:2,websocket:[1,2,3,4,5,6,8,9],well:8,what:8,when:[1,3],whenev:8,where:8,which:[5,8,9],without:9,work:[4,7],ws_host:[1,8,9],ws_pass:[1,8,9],wsclienttestcas:[1,2,4,6],you:[1,10]},titles:["ApiDoc","producer package","producer.events package","producer.heartbeats package","producer.love_csc package","producer.scriptqueue package","producer.telemetries package","Welcome to LOVE-producer\u2019s documentation!","How it works","Overview and configuration","Readme File"],titleterms:{The:8,Use:10,apidoc:0,base_ws_cli:1,build:10,choos:9,client:[2,3,4,5,6],command:8,commun:9,config:9,configur:9,content:[1,2,3,4,5,6],csc:[4,8,9],develop:10,docker:10,document:[7,10],environ:9,event:[2,8],file:[8,10],get:10,heartbeat:[3,8],how:8,imag:10,indic:7,initi:8,json:9,load:10,local:10,love:[7,8,9,10],love_csc:4,main:[1,8],modul:[1,2,3,4,5,6],overview:9,packag:[1,2,3,4,5,6],part:10,produc:[1,2,3,4,5,6,7,8,9,10],readm:10,receiv:8,run:10,sal:9,scriptqueu:[5,8],state:8,submodul:[1,2,3,4,5,6],subpackag:1,system:10,tabl:7,telemetri:[6,8],test:10,test_avail:5,test_client:[2,6],test_csc:4,test_produc:[2,3,6],test_scripts_heartbeat:5,test_stat:5,test_util:1,topic:9,util:1,variabl:9,welcom:7,work:8}})