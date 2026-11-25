#!/usr/bin/env python3
"""Patch the recovered Laya H5 client for a local-only first boot."""
from __future__ import annotations
import argparse
from pathlib import Path

HOOK = r"""
;/* SUPER_SPIRIT_BALL_OFFLINE_PATCH_V1 */
(function(){
  "use strict";
  var KEY="super-spirit-ball-offline-save-v1", UID=730001, NAME="离线训练师";
  var log=function(){try{console.log.apply(console,["[Offline]"].concat([].slice.call(arguments)));}catch(e){}};
  // Laya stores atlas frame URLs in Loader.atlasMap, not in the
  // ordinary getRes cache. The old check used the wrong cache and skipped
  // frame registration even when ani1.atlas had loaded successfully.
  function registerOfflineJgAtlasFrames(atlasUrl){
    var loaderClass=typeof laya!=="undefined"&&laya.net&&laya.net.Loader;
    var atlasTextures=loaderClass&&loaderClass.getAtlas(atlasUrl);
    if(!atlasTextures||!atlasTextures.length)return false;
    Laya.Animation.createFrames(atlasUrl,"jg");
    var frames=Laya.Animation.framesMap&&Laya.Animation.framesMap.jg;
    if(!frames||!frames.length)return false;
    log("local ani1 atlas frames registered",frames.length,atlasTextures.length);
    return true;
  }
  try{
    var combatResManager=typeof game!=="undefined"&&game.combat&&game.combat.CombatResManager;
    if(combatResManager&&combatResManager.prototype&&!combatResManager.prototype.__offlineJgAtlasFix){
      var originalLoadResInCombat=combatResManager.prototype.loadResInCombat;
      combatResManager.prototype.loadResInCombat=function(){
        var result=originalLoadResInCombat.apply(this,arguments);
        return Promise.resolve(result).then(function(value){
          var atlasUrl="atlas/combat/ani1.atlas";
          try{
            if(registerOfflineJgAtlasFrames(atlasUrl))return value;
            log("local ani1 atlas index missing after combat preload; retrying",atlasUrl);
            return new Promise(function(resolve){
              var settled=false;
              var finish=function(){
                if(settled)return;
                settled=true;
                clearTimeout(timer);
                try{
                  if(!registerOfflineJgAtlasFrames(atlasUrl))
                    log("local ani1 atlas frames unavailable after retry",atlasUrl);
                }catch(e){log("local ani1 atlas init error",e&&e.stack||e);}
                resolve(value);
              };
              var timer=setTimeout(function(){
                log("local ani1 atlas retry timed out; continuing battle",atlasUrl);
                finish();
              },8000);
              try{
                Laya.loader.load(atlasUrl,new Laya.Handler(null,finish),null,"atlas");
              }catch(e){
                log("local ani1 atlas retry error",e&&e.stack||e);
                finish();
              }
            });
          }catch(e){
            log("local ani1 atlas init error",e&&e.stack||e);
            return value;
          }
        });
      };
      combatResManager.prototype.__offlineJgAtlasFix=true;
    }
  }catch(e){log("offline combat atlas patch",e&&e.stack||e);}
  window.addEventListener("unhandledrejection",function(e){log("unhandledrejection",e.reason&&e.reason.stack||e.reason);});
  window.addEventListener("error",function(e){log("window error",e.message,e.filename,e.lineno,e.error&&e.error.stack);});
  // The original pet panels reference loose PNGs but never shipped these
  // optional atlas bundles. Skip the empty bundles; their PNGs are packaged
  // from zip.txt and remain available for direct loading.
  try{
    var groupProto=typeof ResGroupConfig!=="undefined"&&ResGroupConfig.prototype;
    if(groupProto&&typeof groupProto.getAssetList==="function"&&!groupProto.__offlineOptionalAtlasFix){
      var getAssetList=groupProto.getAssetList;
      groupProto.getAssetList=function(name){
        if(name==="ZPower"||name==="upgradeLight"){
          log("local optional atlas group skipped",name);
          return [];
        }
        return getAssetList.apply(this,arguments);
      };
      groupProto.__offlineOptionalAtlasFix=true;
    }
  }catch(e){log("optional pet atlas group patch",e&&e.stack||e);}
  // The archived server no longer has upgradeLight/1..9.png. The effect is
  // cosmetic; suppress its animation instead of requesting nine dead URLs.
  try{
    var UpgradeLight=typeof Common!=="undefined"&&Common.UpgradeLight;
    if(UpgradeLight&&UpgradeLight.prototype&&!UpgradeLight.prototype.__offlineNoUpgradeLight){
      UpgradeLight.prototype.play=function(){
        this.visible=false;
        log("local upgrade flash animation skipped: original frames unavailable");
        return this;
      };
      UpgradeLight.prototype.__offlineNoUpgradeLight=true;
    }
  }catch(e){log("optional upgrade flash patch",e&&e.stack||e);}
  var read=function(){
    try{
      var o=JSON.parse(localStorage.getItem(KEY)||"null");
      if(o&&o.proto){
        var raw=atob(o.proto), bytes=new Uint8Array(raw.length);
        for(var i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
        o.restored=rp.UserDataInfo.decode(bytes);
      }
      return o;
    }catch(e){log("save restore error",e);return null;}
  };
  var saved=read()||{}, current=null;
  function offlineDateKey(d){
    d=d||new Date();
    return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  }
  function offlineWeekKey(d){
    d=new Date(d||Date.now());d.setHours(0,0,0,0);
    d.setDate(d.getDate()-((d.getDay()+6)%7));
    return offlineDateKey(d);
  }
  var offlineTaskMeta=saved.offlineTaskMeta||{};
  var offlineToday=offlineDateKey(),offlineWeek=offlineWeekKey();
  var offlineDayReset=offlineTaskMeta.dayKey!==offlineToday;
  var offlineWeekReset=offlineTaskMeta.weekKey!==offlineWeek;
  if(offlineDayReset){offlineTaskMeta.dayKey=offlineToday;offlineTaskMeta.dailyCounters={};}
  if(offlineWeekReset){offlineTaskMeta.weekKey=offlineWeek;offlineTaskMeta.weeklyCounters={};}
  if(!offlineTaskMeta.dailyCounters)offlineTaskMeta.dailyCounters={};
  if(!offlineTaskMeta.weeklyCounters)offlineTaskMeta.weeklyCounters={};
  if(!offlineTaskMeta.lastHangupTime)offlineTaskMeta.lastHangupTime=Math.floor(Date.now()/1000)-3600;
  var expectedHangupRestore=Number(offlineTaskMeta.expectedHangupRestoreTime)||0;
  var hangupRestoredAfterDayReset=offlineDayReset&&expectedHangupRestore>0&&
    Number(offlineTaskMeta.lastHangupTime)===expectedHangupRestore&&
    Number(offlineTaskMeta.dailyCounters[52]||0)===0;
  var quickCombatUsed=offlineDayReset?0:(Number(saved.quickCombatUsed)||0);
  var long=function(v){try{if($util.Long)return $util.Long.fromString(String(v),true);}catch(e){}return Number(v)||0;};
  function currentCardSeason(){
    try{
      var a=GC.G().CARD_COLLECT_SEASON_CONF.getDesList(),now=Date.now()/1000,chosen=null;
      for(var i=0;i<a.length;i++)if(a[i].startTime<=now&&now<a[i].endTime){chosen=a[i];break;}
      return chosen?chosen.seasonId:(a.length?a[a.length-1].seasonId:1);
    }catch(e){log("season fallback",e);return 19;}
  }
  function normalizeGuideSchedule(u){
    if(!u.guideScheduleInfo)u.guideScheduleInfo={};
    if(!u.guideScheduleInfo.riseStepByStep)u.guideScheduleInfo.riseStepByStep={};
    u.guideScheduleInfo.riseStepByStep.isFinish=1;
    if(!u.guideScheduleInfo.pokemonComing)u.guideScheduleInfo.pokemonComing={};
    u.guideScheduleInfo.pokemonComing.isFinish=1;
    if(!u.guideScheduleInfo.challenges)u.guideScheduleInfo.challenges=[];
    if(!u.activityInfo)u.activityInfo=new rp.ActivityInfo();
    if(!u.activityInfo.trialTowerInfo)u.activityInfo.trialTowerInfo=new rp.TrialTowerInfo();
    if(!u.activityInfo.trialTowerInfo.levels)u.activityInfo.trialTowerInfo.levels={};
    if(!u.activityInfo.divinationTrialInfo)u.activityInfo.divinationTrialInfo=new rp.DivinationTrialInfo();
    if(!u.activityInfo.divinationTrialInfo.tasks)u.activityInfo.divinationTrialInfo.tasks={};
    if(!u.extInfo)u.extInfo=new rp.UserExtInfo();
    if(!u.extInfo.newStoreRechargeInfo)u.extInfo.newStoreRechargeInfo=new rp.NewStoreRechargeInfo();
    if(!u.extInfo.newStoreRechargeInfo.fundInfo)u.extInfo.newStoreRechargeInfo.fundInfo={};
    if(!u.extInfo.newStoreRechargeInfo.petSetMeal)u.extInfo.newStoreRechargeInfo.petSetMeal={};
    if(!u.extInfo.chaseBeastInfo)u.extInfo.chaseBeastInfo=new rp.ChaseBeastInfo();
    if(!u.extInfo.chaseBeastInfo.chaseBeastGuardInfo)u.extInfo.chaseBeastInfo.chaseBeastGuardInfo={};
  }
  function petFrom(p){
    var x=new rp.PetEntry();
    try{if(p)for(var key in p)if(Object.prototype.hasOwnProperty.call(p,key))x[key]=p[key];}catch(_){}
    var id=Number(p&&p.id)||3101,cfg=null;
    try{cfg=GC.G().spiritConfig.getDes(id);}catch(_){}
    x.id=id;x.level=Math.max(1,Number(p&&p.level)||1);x.genId=Number(p&&p.genId)||100001;
    x.name=p&&p.name||cfg&&cfg.name||"天空领主";x.exp=Number(p&&p.exp)||0;
    if(cfg){
      if(!Number(x.hp))x.hp=long(Number(cfg.hp)||0);
      if(!Number(x.attack))x.attack=long(Number(cfg.attack)||0);
      if(!Number(x.defense))x.defense=long(Number(cfg.defense)||0);
      if(!Number(x.starLevel))x.starLevel=Number(cfg.quality)||Number(cfg.starLevel)||1;
    }
    if(!Number(x.fightScore)){
      x.fightScore=long(Math.floor(1.1*Number(x.hp||0)+10*Number(x.attack||0)+10*Number(x.defense||0)));
    }
    log("local pet seed attrs",id,String(x.attack),String(x.defense),String(x.hp));
    log("local pet seed score",id,String(x.fightScore));
    return x;
  }
  function normalizePetPack(u){
    if(!u.petPackInfo)u.petPackInfo=new rp.PetPackInfo();
    var packs=u.petPackInfo.packArray;
    if(!Array.isArray(packs))packs=[];
    var first=packs[0]&&packs[0].pet;
    if(!first||!first.id)first=petFrom(null);
    // The original client supports three formations with six positions each.
    // Its DataManager setter rebuilds exactly 18 slots.
    for(var i=0;i<18;i++){
      var node=packs[i];
      if(!node){node=new rp.PackNode();node.state=0;node.equip=[];node.combatPos=0;}
      if(!node.equip)node.equip=[];
      node.index=i+1;
      if(node.pet&&node.pet.id)node.state=1;
      else{node.state=0;node.combatPos=0;}
      if(i===0&&(!node.pet||!node.pet.id)){node.pet=first;node.state=1;node.combatPos=1;}
      packs[i]=node;
    }
    packs.length=18;
    u.petPackInfo.packArray=packs;
    if(!u.petStorageInfo)u.petStorageInfo=new rp.PetStorageInfo();
    if(!Array.isArray(u.petStorageInfo.petArray))u.petStorageInfo.petArray=[];
    if(!u.petStorageInfo.petArray.some(function(x){return x&&x.genId===first.genId;}))u.petStorageInfo.petArray.push(first);
    if(!u.petStorageInfo.sidGenerator)u.petStorageInfo.sidGenerator=100002;
    return packs;
  }
  function offlinePackSlot(index){
    var n=Number(index);
    if(!isFinite(n)||Math.floor(n)!==n)return -1;
    return n>0?n-1:n;
  }
  function offlineClientPet(p,inPack){
    var c=new rp.ClientPetEntry();
    var fields=["id","name","level","catchTime","isNew","oldHp","oldDefense","oldAttack","genId","exp","insight","evalve","shadowPet",
      "assitAttack","assitDefense","assitHp","washHp","washAttack","washDefense","washLevel","washStates","washNewHp","washNewAttack","washNewDefense",
      "washStoneCountLow","washStoneCountHigh","awakeTimes","fosterAttrIdNum","fosterAttrMap","isskinon","isBreakLimit","attack","defense","hp","starLevel","crystalLevel","fightScore","zPower"];
    fields.forEach(function(k){if(p&&p[k]!=null)c[k]=p[k];});
    c.__isInPack=inPack?1:0;
    return c;
  }
  function makeOfflinePetStorageRsp(r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    current=u;normalizePetPack(u);
    var storage=u.petStorageInfo,pack=u.petPackInfo,seen={},petArray=[];
    (storage.petArray||[]).forEach(function(p){
      if(!p||!p.genId||seen[p.genId])return;
      seen[p.genId]=true;
      var equipped=pack.packArray.some(function(n){return n&&n.pet&&n.pet.genId===p.genId;});
      petArray.push(offlineClientPet(p,equipped));
    });
    pack.packArray.forEach(function(n){
      var p=n&&n.pet;
      if(!p||!p.genId||seen[p.genId])return;
      seen[p.genId]=true;petArray.push(offlineClientPet(p,true));
    });
    var clientStorage=new rp.ClientPetStorageInfo();
    clientStorage.sidGenerator=storage.sidGenerator||100002;clientStorage.petArray=petArray;
    r.ret=0;r.storageInfo=storage;r.packInfo=pack;r.unlockLevel=r.unlockLevel||[];
    r.maxStoragePstCount=100;r.clientStorageInfo=clientStorage;
    log("local pet storage loaded",petArray.length,pack.packArray.length);
    return r;
  }
  function makeOfflinePackMutation(req,kind,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    current=u;var packs=normalizePetPack(u),a,b;
    if(kind==="formationChange"){
      a=offlinePackSlot(req&&req.index);b=Number(req&&req.pos);
      if(a<0||a>=18||b<1||b>6||!packs[a]||!packs[a].pet){r.ret=1;return r;}
      var row=Math.floor(a/6)*6;
      for(var i=row;i<row+6;i++)if(i!==a&&packs[i]&&Number(packs[i].combatPos)===b)packs[i].combatPos=0;
      packs[a].combatPos=b;
    }else if(kind==="packSwap"){
      a=offlinePackSlot(req&&req.petIndex1);b=offlinePackSlot(req&&req.petIndex2);
      if(a<0||a>=18||b<0||b>=18){r.ret=1;return r;}
      var left=packs[a],right=packs[b];
      ["state","pet","equip","combatPos","artifact","indexFateMap","pvePetId"].forEach(function(k){var v=left[k];left[k]=right[k];right[k]=v;});
      left.index=a+1;right.index=b+1;
    }else if(kind==="formationSwap"){
      a=Number(req&&req.formationIndex1);b=Number(req&&req.formationIndex2);
      if(a<0||a>2||b<0||b>2){r.ret=1;return r;}
      for(var j=0;j<6;j++){
        var ia=a*6+j,ib=b*6+j,one=packs[ia],two=packs[ib];
        ["state","pet","equip","combatPos","artifact","indexFateMap","pvePetId"].forEach(function(k){var v=one[k];one[k]=two[k];two[k]=v;});
        one.index=ia+1;two.index=ib+1;
      }
    }else if(kind==="takePet"){
      a=offlinePackSlot(req&&req.packIndex);
      var petId=Number(req&&req.petId),pet=(u.petStorageInfo.petArray||[]).find(function(p){return p&&Number(p.genId)===petId;});
      if(a<0||a>=18||!pet){r.ret=1;return r;}
      var alreadyPacked=packs.some(function(n,i){return i!==a&&n&&n.pet&&Number(n.pet.genId)===petId;});
      if(alreadyPacked){r.ret=1;log("local pet already in pack",petId);return r;}
      packs[a].pet=petFrom(pet);packs[a].state=1;packs[a].combatPos=a%6+1;
    }else if(kind==="cleanPet"){
      a=offlinePackSlot(req&&req.index);
      if(a<0||a>=18||!packs[a]||!packs[a].pet){r.ret=1;return r;}
      packs[a].pet=null;packs[a].state=0;packs[a].combatPos=0;packs[a].equip=[];packs[a].artifact=null;
    }
    u.petPackInfo=new rp.PetPackInfo();u.petPackInfo.packArray=packs;
    if(typeof DM!=="undefined"&&DM.G&&DM.G().setPetPackInfo)DM.G().setPetPackInfo(u.petPackInfo);
    r.ret=0;if(r.packInfo!==undefined)r.packInfo=u.petPackInfo;
    if(r.storageInfo!==undefined)r.storageInfo=u.petStorageInfo;
    save();log("local pet pack mutation",kind,a,b,packs.length);
    return r;
  }
  function offlineAction(type,params){
    var a=new rp.Action();a.type=type;a.params=params||[];return a;
  }
  function offlineTaskConfig(name,id){
    try{
      var cfg=GC.G()[name],value=cfg&&cfg.getDes(Number(id));
      return value||null;
    }catch(e){return null;}
  }
  function offlineTaskList(name){
    try{var cfg=GC.G()[name],rows=cfg&&cfg.getDesList();return Array.isArray(rows)?rows:[];}
    catch(e){return [];}
  }
  function ensureOfflineTaskInfo(u){
    if(!u)return null;
    var info=u.newTaskInfo;
    if(!info||typeof info!=="object")info=u.newTaskInfo=new rp.DBNewTaskInfo();
    if(offlineDayReset||!info.dailyTask){info.dailyTask=new rp.NewDailyTask();offlineDayReset=false;}
    if(offlineWeekReset||!info.weekTask){info.weekTask=new rp.NewWeekTask();offlineWeekReset=false;}
    if(!info.training)info.training=new rp.TaskTrainning();
    if(!info.mainTask)info.mainTask=new rp.NewMainTask();
    if(!info.dailyTask.tasks)info.dailyTask.tasks={};
    if(!info.weekTask.tasks)info.weekTask.tasks={};
    if(!info.mainTask.tasks)info.mainTask.tasks={};
    if(!info.mainTask.activeGroups)info.mainTask.activeGroups={};
    if(!info.mainTask.groupParams)info.mainTask.groupParams={};
    offlineTaskList("NEW_DAY_TASK_CONF").forEach(function(cfg){
      var id=Number(cfg.taskId);
      if(!info.dailyTask.tasks[id])info.dailyTask.tasks[id]=new rp.NewTaskNode();
    });
    offlineTaskList("NEW_WEEK_TASK_CONF").forEach(function(cfg){
      var id=Number(cfg.taskId);
      if(!info.weekTask.tasks[id])info.weekTask.tasks[id]=new rp.NewTaskNode();
    });
    // The offline client implements the main-story task chain. Other task
    // groups require unavailable arena/guild/shop servers and are not fabricated.
    var mainRows=offlineTaskList("NEW_MAIN_TASK_CONF").filter(function(cfg){return Number(cfg.groupId)===1;});
    if(mainRows.length){
      var ids=Object.keys(info.mainTask.tasks).map(Number).filter(function(id){
        var cfg=offlineTaskConfig("NEW_MAIN_TASK_CONF",id);return cfg&&Number(cfg.groupId)===1;
      }).sort(function(a,b){return a-b;});
      if(!ids.length){
        var first=mainRows[0].taskId;
        info.mainTask.tasks[first]=new rp.NewTaskNode();
        ids=[Number(first)];
      }
      var currentId=ids[ids.length-1],currentNode=info.mainTask.tasks[currentId];
      if(currentNode&&Number(currentNode.status)>0){
        var next=offlineTaskConfig("NEW_MAIN_TASK_CONF",currentId+1);
        if(next&&Number(next.groupId)===1&&!info.mainTask.tasks[currentId+1]){
          info.mainTask.tasks[currentId+1]=new rp.NewTaskNode();
          currentId++;
        }
      }
      info.mainTask.activeGroups[1]=currentId;
    }
    syncOfflineTaskProgress(u);
    return info;
  }
  function syncOfflineTaskProgress(u){
    if(!u||!u.newTaskInfo)return;
    var info=u.newTaskInfo;
    var daily=info.dailyTask,weekly=info.weekTask,main=info.mainTask;
    if(daily&&daily.tasks){
      offlineTaskList("NEW_DAY_TASK_CONF").forEach(function(cfg){
        var node=daily.tasks[cfg.taskId];if(!node)return;
        var type=Number(cfg.cond&&cfg.cond.taskType),count=0;
        if(type===47)count=1;
        else if(type===40)count=Number(offlineTaskMeta.dailyCounters[40])||0;
        else if(type===49)count=Number(offlineTaskMeta.dailyCounters[49])||0;
        else if(type===52)count=Number(offlineTaskMeta.dailyCounters[52])||0;
        node.finishNum=Math.max(Number(node.finishNum)||0,Math.min(Number(cfg.cond&&cfg.cond.needNum)||0,count));
      });
    }
    if(weekly&&weekly.tasks){
      offlineTaskList("NEW_WEEK_TASK_CONF").forEach(function(cfg){
        var node=weekly.tasks[cfg.taskId];if(!node)return;
        var type=Number(cfg.cond&&cfg.cond.taskType),count=type===47?1:(Number(offlineTaskMeta.weeklyCounters[type])||0);
        node.finishNum=Math.max(Number(node.finishNum)||0,Math.min(Number(cfg.cond&&cfg.cond.needNum)||0,count));
      });
    }
    if(main&&main.tasks){
      var ids=Object.keys(main.tasks).map(Number).filter(function(id){
        var cfg=offlineTaskConfig("NEW_MAIN_TASK_CONF",id);return cfg&&Number(cfg.groupId)===1;
      }).sort(function(a,b){return a-b;});
      var activeId=ids.length?ids[ids.length-1]:0;
      if(activeId){
        var node=main.tasks[activeId],cfg=offlineTaskConfig("NEW_MAIN_TASK_CONF",activeId);
        var target=Number(cfg&&cfg.cond&&cfg.cond.params&&cfg.cond.params[0])||0;
        var stage=Number(u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneLevel)||1;
        if(node&&Number(node.status)===0&&target>0&&stage>=target)
          node.finishNum=Math.max(Number(node.finishNum)||0,Number(cfg.cond.needNum)||1);
        main.activeGroups[1]=activeId;
      }
    }
  }
  function offlineConfigActions(actions){
    return (Array.isArray(actions)?actions:[]).map(function(a){
      return offlineAction(Number(a.type),Array.isArray(a.params)?a.params.slice():[]);
    });
  }
  function applyOfflineActions(actions){
    (actions||[]).forEach(function(a){applyLocalRewardAction(a);});
  }
  function makeOfflineTaskOperate(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    current=u;
    var info=ensureOfflineTaskInfo(u),op=Number(req&&req.operate),id=Number(req&&req.confId)||0;
    r.ret=0;r.awards=[];r.newTaskInfo=info;
    if(op===0){
      log("local NewTaskInfoOperate 0 daily",Object.keys(info.dailyTask.tasks).length,
        "week",Object.keys(info.weekTask.tasks).length,
        "main",Object.keys(info.mainTask.tasks).length);
      save();return r;
    }
    if(op===1||op===3){
      var isDaily=op===1;
      var cfg=offlineTaskConfig(isDaily?"NEW_DAY_TASK_CONF":"NEW_WEEK_TASK_CONF",id);
      var task=isDaily?info.dailyTask:info.weekTask;
      var node=task&&task.tasks&&task.tasks[id];
      if(!cfg||!node||Number(node.status)>0||
        Number(node.finishNum)<Number(cfg.cond&&cfg.cond.needNum||1)){
        r.ret=1;log("local task claim rejected",op,id,node&&node.finishNum);return r;
      }
      node.status=1;
      var liveness=Math.max(0,Number(cfg.addLiveness)||0);
      if(isDaily){
        task.dayLiveness=(Number(task.dayLiveness)||0)+liveness;
        info.training.liveness=(Number(info.training.liveness)||0)+liveness;
        r.awards=[offlineAction(rp.Action.ActionTye.ADD_POINT_ITEM,[78,liveness])];
        addLocalPointItem(78,liveness);
      }else{
        task.weekLiveness=(Number(task.weekLiveness)||0)+liveness;
        r.awards=[offlineAction(rp.Action.ActionTye.ADD_POINT_ITEM,[79,liveness])];
        addLocalPointItem(79,liveness);
      }
      log("local task claimed",isDaily?"daily":"weekly",id,"liveness",liveness);
    }else if(op===2||op===4){
      var isDailyBox=op===2;
      var boxList=offlineTaskList("NEW_TASK_BOX_CONF").filter(function(x){
        return isDailyBox?x.taskType==null:Number(x.taskType)===1;
      }).sort(function(a,b){return Number(a.id)-Number(b.id);});
      var boxIndex=boxList.findIndex(function(x){return Number(x.id)===id;});
      var targetTask=isDailyBox?info.dailyTask:info.weekTask;
      var livenessValue=Number(isDailyBox?targetTask.dayLiveness:targetTask.weekLiveness)||0;
      var bit=boxIndex>=0?Math.pow(2,boxIndex):0;
      if(boxIndex<0||!targetTask||(Number(targetTask.boxStatus||0)&bit)!==0||
        livenessValue<Number(boxList[boxIndex].needLiveness||0)){
        r.ret=1;log("local task box claim rejected",op,id,livenessValue);return r;
      }
      targetTask.boxStatus=(Number(targetTask.boxStatus)||0)|bit;
      r.awards=offlineConfigActions(boxList[boxIndex].actions);
      applyOfflineActions(r.awards);
      log("local task box claimed",isDailyBox?"daily":"weekly",id,"liveness",livenessValue);
    }else if(op===6){
      var mainCfg=offlineTaskConfig("NEW_MAIN_TASK_CONF",id);
      var mainNode=info.mainTask&&info.mainTask.tasks&&info.mainTask.tasks[id];
      if(!mainCfg||Number(mainCfg.groupId)!==1||!mainNode||Number(mainNode.status)>0||
        Number(mainNode.finishNum)<Number(mainCfg.cond&&mainCfg.cond.needNum||1)){
        r.ret=1;log("local main task claim rejected",id,mainNode&&mainNode.finishNum);return r;
      }
      mainNode.status=1;
      r.awards=offlineConfigActions(mainCfg.actions);
      applyOfflineActions(r.awards);
      var nextCfg=offlineTaskConfig("NEW_MAIN_TASK_CONF",id+1);
      if(nextCfg&&Number(nextCfg.groupId)===1&&!info.mainTask.tasks[id+1])
        info.mainTask.tasks[id+1]=new rp.NewTaskNode();
      info.mainTask.activeGroups[1]=nextCfg&&Number(nextCfg.groupId)===1?id+1:id;
      syncOfflineTaskProgress(u);
      log("local main task claimed",id,"next",nextCfg&&Number(nextCfg.groupId)===1?id+1:0);
    }else{
      // Training unlock/paid claims stay disabled: no payment or premium-service
      // success is fabricated in an offline build.
      r.ret=1;log("local task operation unsupported",op,id);
      return r;
    }
    r.newTaskInfo=info;
    save();
    return r;
  }
  function makeOfflineHangupRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    current=u;
    var now=Math.floor(Date.now()/1000),last=Number(offlineTaskMeta.lastHangupTime)||now-3600;
    var elapsed=Math.max(0,now-last);
    var next=offlineTaskConfig("NEW_SCENE_GRADE_CONF",(Number(u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneLevel)||1)+1);
    var level=Number(next&&next.level)||1;
    var cfg=offlineTaskConfig("HANGUP_DETAILS_CONF",level);
    var ready=elapsed>=60,operate=Number(req&&req.operate)||0;
    r.ret=0;r.lastHangupTime=last;r.awards=ready&&cfg?offlineConfigActions(cfg.actionArr):[];
    if(operate>0){
      if(!ready||!cfg){r.ret=1;r.awards=[];return r;}
      applyOfflineActions(r.awards);
      offlineTaskMeta.lastHangupTime=now;
      offlineTaskMeta.dailyCounters[52]=(Number(offlineTaskMeta.dailyCounters[52])||0)+1;
      r.lastHangupTime=now;
      log("local HangupOperate claimed",level,"elapsed",elapsed,"awards",r.awards.length,
        "dailyClaims",offlineTaskMeta.dailyCounters[52]);
      save();
    }else{
      log("local HangupOperate query",level,"elapsed",elapsed,"ready",ready);
    }
    return r;
  }
  function makeOfflineQuickHangupRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    current=u;
    var stage=Number(u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneLevel)||1,
      next=offlineTaskConfig("NEW_SCENE_GRADE_CONF",stage+1),
      level=Number(next&&next.level)||1,
      cfg=offlineTaskConfig("HANGUP_DETAILS_CONF",level),
      operate=Number(req&&req.operate)||0;
    r.todayUseCount=quickCombatUsed;r.maxDayUseCount=1;
    r.todayBuyCount=0;r.maxDayBuyCount=0;
    r.awards=cfg?offlineConfigActions(cfg.actionArr):[];
    if(!cfg||!Array.isArray(cfg.actionArr)||!cfg.actionArr.length){
      r.ret=1;r.awards=[];
      log("local QuickHangupOperate rejected: reward config missing",stage,level);
      return r;
    }
    if(operate===0){
      r.ret=0;
      log("local QuickHangupOperate query",level,"used",quickCombatUsed,"rewards",r.awards.length);
      return r;
    }
    if(operate!==1||quickCombatUsed>=1){
      r.ret=1;r.awards=[];
      log("local QuickHangupOperate rejected",operate,"used",quickCombatUsed);
      return r;
    }
    applyOfflineActions(r.awards);
    quickCombatUsed=1;
    offlineTaskMeta.dailyCounters[49]=(Number(offlineTaskMeta.dailyCounters[49])||0)+1;
    syncOfflineTaskProgress(u);
    r.ret=0;r.todayUseCount=quickCombatUsed;
    log("local QuickHangupOperate claimed",level,"used",quickCombatUsed,
      "rewards",r.awards.length);
    save();
    return r;
  }
  function addLocalGold(amount){
    try{
      var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
      if(!u||!u.baseInfo)return;
      if(!u.baseInfo.moneyInfo)u.baseInfo.moneyInfo=new rp.MoneyInfo();
      var m=u.baseInfo.moneyInfo;m.gold=long(Number(m.gold||0)+Number(amount||0));
      log("local gold reward",amount,String(m.gold));save();
    }catch(e){log("local gold update",e&&e.stack||e);}
  }
  function addLocalPointItem(id,amount){
    try{
      var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
      if(!u||!u.baseInfo)return;
      var map=u.baseInfo.newPointItemMap||(u.baseInfo.newPointItemMap={});
      id=Number(id);amount=Number(amount)||0;
      map[id]=Math.max(0,Number(map[id])||0)+amount;
      log("local point item reward",id,amount,map[id]);
    }catch(e){log("local point item update",e&&e.stack||e);}
  }
  function localItemConfig(id){
    try{return util.UConfig.getItemCfg(Number(id));}catch(_){}
    try{return GC.G().itemConfig.getDes(Number(id));}catch(_){}
    return null;
  }
  function localEquipmentPosition(id){
    var cfg=localItemConfig(id);
    if(!cfg||Number(cfg.type)!==3)return 0;
    var pos=Number(cfg.position)||0;
    return pos>=1&&pos<=4?pos:0;
  }
  function localEquipmentScore(item){
    var cfg=localItemConfig(item&&item.id),attrs=cfg&&cfg.attr||[];
    var value=0;
    for(var i=0;i<attrs.length;i++)value+=Math.abs(Number(attrs[i].addValue)||0);
    return (Number(cfg&&cfg.grade)||0)*1000000+value;
  }
  function localLongValue(value){
    try{
      if(value&&typeof value==="object"&&value.low!=null&&value.high!=null&&$util.Long){
        return $util.Long.fromBits(Number(value.low)||0,Number(value.high)||0,value.unsigned!==false);
      }
    }catch(e){log("local sid restore conversion",e);}
    return long(value);
  }
  function localNormalizeItemBase(raw){
    if(!raw)return raw;
    var item=raw;
    if(!(item instanceof rp.ItemBase)){
      item=new rp.ItemBase();
      Object.keys(raw).forEach(function(k){item[k]=raw[k];});
    }
    if(item.sid!=null)item.sid=localLongValue(item.sid);
    if(item.equipInfo&&!(item.equipInfo instanceof rp.ItemBaseEquip)){
      var info=new rp.ItemBaseEquip();
      Object.keys(item.equipInfo).forEach(function(k){info[k]=item.equipInfo[k];});
      item.equipInfo=info;
    }
    if(item.genId==null)item.genId=Number(item.sid)||0;
    return item;
  }
  function localNextItemSid(pack){
    var next=Math.max(100002,Math.floor(Number(pack.sidGenerator)||100002));
    while(pack.sidMap[String(next)])next++;
    pack.sidGenerator=localLongValue(next+1);
    return localLongValue(next);
  }
  function localMakeEquipmentItem(id,pack,template){
    var item=new rp.ItemBase();
    item.id=Number(id);item.sid=localNextItemSid(pack);item.count=1;
    item.starLevel=Number(template&&template.starLevel)||0;
    item.equipInfo=new rp.ItemBaseEquip();
    item.equipInfo.strengLevel=Number(template&&template.equipInfo&&template.equipInfo.strengLevel)||0;
    item.equipInfo.magicLevel=Number(template&&template.equipInfo&&template.equipInfo.magicLevel)||0;
    item.equipInfo.magicExp=Number(template&&template.equipInfo&&template.equipInfo.magicExp)||0;
    item.equipInfo.itemId=template&&template.equipInfo&&template.equipInfo.itemId||[];
    item.equipInfo.equipIndex=localEquipmentPosition(id);
    item.genId=Number(item.sid);
    pack.sidMap[String(item.sid)]=item;
    return item;
  }
  function refreshLocalItemIndexes(u){
    try{
      var dm=typeof DM!=="undefined"&&DM.G&&DM.G();
      if(!dm||!u||!u.itemPackInfo)return;
      var pack=u.itemPackInfo,all=[],byId={};
      function append(item){
        if(!item)return;
        all.push(item);
        byId[Number(item.id)]=item;
      }
      Object.keys(pack.idMap||{}).forEach(function(k){append(pack.idMap[k]);});
      Object.keys(pack.sidMap||{}).forEach(function(k){append(pack.sidMap[k]);});
      dm.itemPackInfos=all;dm.itemIdMap=byId;
    }catch(e){log("local item index rebuild",e&&e.stack||e);}
  }
  function normalizeLocalEquipmentInventory(u){
    if(!u)return;
    if(!u.itemPackInfo)u.itemPackInfo=new rp.ItemPackInfo();
    var pack=u.itemPackInfo;
    if(!pack.idMap)pack.idMap={};
    if(!pack.sidMap)pack.sidMap={};
    // Older offline saves stored equipment in idMap as stackable items.
    // Convert those counts to one uniquely-addressed ItemBase per piece.
    Object.keys(pack.idMap).forEach(function(k){
      var id=Number(k),pos=localEquipmentPosition(id),old=pack.idMap[k];
      if(!pos||!old)return;
      var count=Math.max(0,Math.floor(Number(old.count)||0));
      for(var i=0;i<count;i++)localMakeEquipmentItem(id,pack,old);
      delete pack.idMap[k];
      log("local equipment inventory migrated",id,count);
    });
    // PackNode.equip is the authoritative worn-equipment list. Keep every
    // worn ItemBase in sidMap as well so inventory and save remain stable.
    var packs=u.petPackInfo&&u.petPackInfo.packArray||[];
    packs.forEach(function(node){
      if(!node)return;
      if(!Array.isArray(node.equip))node.equip=[];
      node.equip.forEach(function(rawItem,index){
        var item=localNormalizeItemBase(rawItem);
        node.equip[index]=item;
        if(!item||!localEquipmentPosition(item.id))return;
        if(item.sid==null||String(item.sid)==="0"){
          item.sid=localNextItemSid(pack);item.genId=Number(item.sid);
        }
        if(!item.equipInfo)item.equipInfo=new rp.ItemBaseEquip();
        item.equipInfo.equipIndex=localEquipmentPosition(item.id);
        item.count=1;
        pack.sidMap[String(item.sid)]=item;
      });
    });
    Object.keys(pack.sidMap).forEach(function(k){
      var item=localNormalizeItemBase(pack.sidMap[k]);
      if(!item)return;
      if(item.sid==null||String(item.sid)==="0")item.sid=localLongValue(k);
      item.id=Number(item.id)||0;item.count=1;
      if(!item.equipInfo)item.equipInfo=new rp.ItemBaseEquip();
      item.equipInfo.equipIndex=localEquipmentPosition(item.id);
      if(!item.genId)item.genId=Number(item.sid)||0;
      if(String(item.sid)!==String(k))delete pack.sidMap[k];
      pack.sidMap[String(item.sid)]=item;
    });
    refreshLocalItemIndexes(u);
    log("local equipment inventory normalized",
      Object.keys(pack.sidMap).length,Object.keys(pack.idMap).length);
  }
  function addLocalItem(id,amount){
    try{
      var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
      if(!u)return;
      if(!u.itemPackInfo)u.itemPackInfo=new rp.ItemPackInfo();
      if(!u.itemPackInfo.idMap)u.itemPackInfo.idMap={};
      if(!u.itemPackInfo.sidMap)u.itemPackInfo.sidMap={};
      id=Number(id);amount=Math.max(0,Math.floor(Number(amount)||0));
      if(!id||!amount)return;
      var position=localEquipmentPosition(id),last=null;
      if(position){
        normalizeLocalEquipmentInventory(u);
        for(var i=0;i<amount;i++)last=localMakeEquipmentItem(id,u.itemPackInfo,null);
        refreshLocalItemIndexes(u);
        log("local equipment item reward",id,amount,"position",position,
          "sid",last&&String(last.sid));
      }else{
        var item=u.itemPackInfo.idMap[id];
        if(!item)item=u.itemPackInfo.idMap[id]=new rp.ItemBase();
        item.id=id;item.count=Math.max(0,Number(item.count)||0)+amount;
        refreshLocalItemIndexes(u);
        log("local item reward",id,amount,item.count);
      }
    }catch(e){log("local item update",e&&e.stack||e);}
  }
  function localItemBySid(u,sid){
    var map=u&&u.itemPackInfo&&u.itemPackInfo.sidMap||{},key=String(sid);
    if(map[key])return map[key];
    var keys=Object.keys(map);
    for(var i=0;i<keys.length;i++)if(map[keys[i]]&&String(map[keys[i]].sid)===key)return map[keys[i]];
    var packs=u&&u.petPackInfo&&u.petPackInfo.packArray||[];
    for(var p=0;p<packs.length;p++){
      var eq=packs[p]&&packs[p].equip||[];
      for(var j=0;j<eq.length;j++)if(eq[j]&&String(eq[j].sid)===key)return eq[j];
    }
    return null;
  }
  function localEquipmentOwners(u){
    var owners={},packs=u&&u.petPackInfo&&u.petPackInfo.packArray||[];
    packs.forEach(function(node,slot){
      if(!node)return;
      (node.equip||[]).forEach(function(item){
        if(item&&item.sid!=null)owners[String(item.sid)]={
          slot:slot,spiritId:node.pet&&Number(node.pet.id)||0
        };
      });
    });
    return owners;
  }
  function localEquipmentAttrValues(item){
    var cfg=localItemConfig(item&&item.id),out={
      hp:0,attack:0,defense:0,hpPercent:0,attackPercent:0,defensePercent:0
    };
    (cfg&&cfg.attr||[]).forEach(function(a){
      var id=Number(a.attrId),kind=id===12?"hp":id===13?"attack":id===14?"defense":null;
      if(!kind)return;
      var value=Number(a.addValue)||0;
      var level=Math.max(1,Number(item&&item.equipInfo&&item.equipInfo.strengLevel)||1);
      // The original equipment panel scales fixed attributes after level 1.
      if(level>1&&Number(a.addType)!==1)value=Math.floor(value*(level+9)/10);
      if(Number(a.addType)===1)out[kind+"Percent"]+=value/10;
      else out[kind]+=value;
    });
    return out;
  }
  function localEquipmentBonusForNode(node){
    var total={hp:0,attack:0,defense:0,hpPercent:0,attackPercent:0,defensePercent:0};
    (node&&node.equip||[]).forEach(function(item){
      if(!item||!localEquipmentPosition(item.id))return;
      var bonus=localEquipmentAttrValues(item);
      Object.keys(total).forEach(function(k){total[k]+=Number(bonus[k])||0;});
    });
    return total;
  }
  function localApplyEquipmentBonusToAttr(target,bonus){
    target=target||new rp.PkAttrInfo();
    ["hp","attack","defense","hpPercent","attackPercent","defensePercent"].forEach(function(k){
      target[k]=Number(target[k]||0)+(Number(bonus&&bonus[k])||0);
    });
    return target;
  }
  function localMakeEquipSimple(item,spiritId,position){
    var simple=new rp.EquipSimpleInfo();
    simple.itemId=Number(item&&item.id)||0;
    simple.sid=Number(item&&item.sid)||0;
    simple.spiritId=Number(spiritId)||0;
    simple.equipType=Number(position)||localEquipmentPosition(simple.itemId);
    simple.strengLevel=Number(item&&item.equipInfo&&item.equipInfo.strengLevel)||0;
    simple.genId=Number(item&&item.genId)||simple.sid;
    simple.starLevel=Number(item&&item.starLevel)||0;
    simple.attrInfo=localApplyEquipmentBonusToAttr(new rp.PkAttrInfo(),localEquipmentAttrValues(item));
    return simple;
  }
  function localMakeEquipDetail(item,position){
    if(!item)return null;
    var d=new rp.EquipDetailInfo(),cfg=localItemConfig(item.id);
    d.itemId=Number(item.id)||0;d.sid=Number(item.sid)||0;
    d.equipType=Number(position)||localEquipmentPosition(item.id);
    d.starLevel=Number(item.starLevel)||0;
    d.strengInfo=new rp.EquipStrengInfo();
    d.strengInfo.strengLevel=Number(item.equipInfo&&item.equipInfo.strengLevel)||0;
    d.strengInfo.attrInfo=localApplyEquipmentBonusToAttr(
      new rp.PkAttrInfo(),localEquipmentAttrValues(item));
    d.strengInfo.nextAttrInfo=localApplyEquipmentBonusToAttr(
      new rp.PkAttrInfo(),localEquipmentAttrValues(item));
    d.strengInfo.needItemNum=0;
    d.magicInfo=new rp.EquipMagicInfo();d.magicInfo.magicItem=[];
    d.inlayInfo=[];
    d.suitInfo=new rp.EquipSuitInfo();
    d.suitInfo.suitItemInfo=[];d.suitInfo.attrInfo=[];
    return d;
  }
  function localEquipmentRecords(u){
    normalizeLocalEquipmentInventory(u);
    var pack=u.itemPackInfo||{},owners=localEquipmentOwners(u),seen={},items=[];
    Object.keys(pack.sidMap||{}).forEach(function(k){
      var item=pack.sidMap[k];
      if(!item||!localEquipmentPosition(item.id))return;
      var sid=String(item.sid);
      if(seen[sid])return;
      seen[sid]=true;items.push(item);
    });
    (u.petPackInfo&&u.petPackInfo.packArray||[]).forEach(function(node){
      (node&&node.equip||[]).forEach(function(item){
        if(!item||!localEquipmentPosition(item.id))return;
        var sid=String(item.sid);
        if(seen[sid])return;
        seen[sid]=true;items.push(item);
      });
    });
    return items.map(function(item){
      var owner=owners[String(item.sid)]||null;
      return {item:item,owner:owner?owner.spiritId:0,ownerSlot:owner?owner.slot:-1,
        position:localEquipmentPosition(item.id)};
    });
  }
  function localMakeSpiritEquipmentRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    var index=Number(req&&req.index),slot=index-1;
    if(!isFinite(slot)||Math.floor(slot)!==slot||slot<0||slot>=18){r.ret=1;return r;}
    normalizePetPack(u);
    var node=u.petPackInfo.packArray[slot],petId=node&&node.pet&&Number(node.pet.id)||0;
    r.ret=0;r.equipInfoList=(node&&node.equip||[]).filter(function(item){
      return item&&localEquipmentPosition(item.id)>0;
    }).map(function(item){
      return localMakeEquipSimple(item,petId,localEquipmentPosition(item.id));
    });
    log("local equipment worn query",index,r.equipInfoList.length);
    return r;
  }
  function localMakeEquipmentListRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    var type=Number(req&&req.equipType)||0;
    r.ret=0;r.equipInfoList=localEquipmentRecords(u).filter(function(x){
      return !type||x.position===type;
    }).map(function(x){return localMakeEquipSimple(x.item,x.owner,x.position);});
    var worn=r.equipInfoList.filter(function(x){return Number(x&&x.spiritId)>0;});
    var wornFirst=worn[0]||null;
    log("local equipment inventory query",type,r.equipInfoList.length);
    log("local equipment inventory detail",type,r.equipInfoList.length,
      Number(wornFirst&&wornFirst.spiritId)||0,
      "hp",Number(wornFirst&&wornFirst.attrInfo&&wornFirst.attrInfo.hp)||0);
    return r;
  }
  function localApplyEquipmentChange(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    normalizeLocalEquipmentInventory(u);
    var slot=Number(req&&req.index)-1,type=Number(req&&req.equipType),sid=Number(req&&req.sid)||0;
    if(!isFinite(slot)||Math.floor(slot)!==slot||slot<0||slot>=18||type<1||type>4){r.ret=1;return r;}
    var packs=u.petPackInfo.packArray,node=packs[slot];
    if(!node||!node.pet){r.ret=1;return r;}
    if(!Array.isArray(node.equip))node.equip=[];
    var previous=node.equip.find(function(x){return x&&localEquipmentPosition(x.id)===type;})||null;
    var selected=sid?localItemBySid(u,sid):null;
    if(sid&&(!selected||localEquipmentPosition(selected.id)!==type)){
      r.ret=1;log("local equipment change rejected",slot+1,type,sid);return r;
    }
    if(selected&&previous&&String(selected.sid)===String(previous.sid)){
      r.ret=0;r.equipInfo=localMakeEquipDetail(selected,type);return r;
    }
    if(selected){
      packs.forEach(function(other,otherIndex){
        if(!other||otherIndex===slot)return;
        other.equip=(other.equip||[]).filter(function(x){
          return !x||String(x.sid)!==String(selected.sid);
        });
      });
    }
    node.equip=node.equip.filter(function(x){return !x||localEquipmentPosition(x.id)!==type;});
    if(selected){
      if(!selected.equipInfo)selected.equipInfo=new rp.ItemBaseEquip();
      selected.equipInfo.equipIndex=type;selected.count=1;
      node.equip.push(selected);
      r.equipInfo=localMakeEquipDetail(selected,type);
    }else{
      r.equipInfo=previous?localMakeEquipDetail(previous,type):null;
    }
    node.equip.sort(function(a,b){
      return localEquipmentPosition(a&&a.id)-localEquipmentPosition(b&&b.id);
    });
    refreshLocalItemIndexes(u);
    r.ret=0;save();
    log("local equipment changed",slot+1,type,sid?"equip":"unequip",node.equip.length);
    return r;
  }
  function localAutoWearEquipment(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u){r.ret=1;return r;}
    normalizeLocalEquipmentInventory(u);
    var slot=Number(req&&req.index)-1;
    if(!isFinite(slot)||Math.floor(slot)!==slot||slot<0||slot>=18){r.ret=1;return r;}
    var node=u.petPackInfo.packArray[slot];
    if(!node||!node.pet){r.ret=1;return r;}
    var ownerBySid=localEquipmentOwners(u),records=localEquipmentRecords(u);
    var old=node.equip||[],next=[];
    old.forEach(function(item){
      if(item&&!localEquipmentPosition(item.id))next.push(item);
    });
    var changed=false,selectedPositions=[];
    for(var pos=1;pos<=4;pos++){
      var candidates=[];
      records.forEach(function(rec){
        if(rec.position!==pos)return;
        var owner=ownerBySid[String(rec.item.sid)]||null;
        var wornHere=(old||[]).some(function(x){return x&&String(x.sid)===String(rec.item.sid);});
        if(owner&&owner.slot!==slot&&!wornHere)return;
        candidates.push(rec.item);
      });
      var currentItem=old.find(function(item){return item&&localEquipmentPosition(item.id)===pos;});
      if(currentItem&&!candidates.some(function(x){return String(x.sid)===String(currentItem.sid);}))candidates.push(currentItem);
      candidates.sort(function(a,b){return localEquipmentScore(b)-localEquipmentScore(a);});
      var best=candidates[0]||null;
      if(best){
        next.push(best);selectedPositions.push(pos);
        if(!currentItem||String(currentItem.sid)!==String(best.sid))changed=true;
      }else if(currentItem)changed=true;
    }
    node.equip=next;
    node.equip.sort(function(a,b){
      return localEquipmentPosition(a&&a.id)-localEquipmentPosition(b&&b.id);
    });
    var equipped=next.filter(function(x){return x&&localEquipmentPosition(x.id)>0;});
    r.ret=0;r.changeFlag=changed;
    r.equipInfoList=equipped.map(function(item){
      return localMakeEquipSimple(item,Number(node.pet.id),localEquipmentPosition(item.id));
    });
    refreshLocalItemIndexes(u);
    var gearBonus=localEquipmentBonusForNode(node);
    if(changed){
      // Refresh the Spirit screen immediately so occupied equipment slots appear
      // without leaving and reopening the page.
      localNotifyInventoryChanged(u,true);
      save();
    }
    // Exercise the exact conversion used by local PvE after a successful wear.
    // This verifies that item bonuses affect the next battle, not only the detail popup.
    offlinePetFromEntry(node.pet,node);
    log("local equipment auto-wear",slot+1,"equipped",equipped.length,
      "positions",selectedPositions.join(","),
      "bonus",Number(gearBonus.hp)||0,Number(gearBonus.attack)||0,Number(gearBonus.defense)||0);
    return r;
  }
  function localAddPetToStorage(u,id,count,starLevel,level){
    if(!u||!u.petStorageInfo)return false;
    id=Number(id)||0;count=Math.max(0,Math.floor(Number(count)||0));
    if(!id||!count)return false;
    var cfg=null;
    try{cfg=GC.G().spiritConfig.getDes(id);}catch(_){}
    if(!cfg)return false;
    var storage=u.petStorageInfo;
    if(!Array.isArray(storage.petArray))storage.petArray=[];
    if(storage.petArray.length+count>100)return false;
    var next=Math.max(100002,Math.floor(Number(storage.sidGenerator)||100002));
    for(var i=0;i<count;i++){
      while(storage.petArray.some(function(p){return p&&Number(p.genId)===next;}))next++;
      var pet=petFrom({id:id,genId:next,level:Math.max(1,Number(level)||1),starLevel:Number(starLevel)||0});
      if(starLevel)pet.starLevel=Number(starLevel);
      storage.petArray.push(pet);next++;
    }
    storage.sidGenerator=long(next);
    log("local pet added to storage",id,count,Number(starLevel)||0,
      "total",storage.petArray.length);
    return true;
  }
  function applyLocalRewardAction(a){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo||!a)return;
    var p=a.params||[],type=Number(a.type),amount=Number(p[0])||0;
    if(type===Number(rp.Action.ActionTye.ADD_EXP)){
      u.baseInfo.totalExp=long(Number(u.baseInfo.totalExp||0)+amount);
      u.baseInfo.oldTotalExp=long(Number(u.baseInfo.oldTotalExp||0)+amount);
      addLocalPointItem(4,amount);
      log("local trainer exp reward",amount,String(u.baseInfo.totalExp));
    }else if(type===Number(rp.Action.ActionTye.ADD_PET_EXP)){
      addLocalPointItem(5,amount);
      log("local pet exp reward",amount,Number(u.baseInfo.newPointItemMap&&u.baseInfo.newPointItemMap[5]||0));
    }else if(type===Number(rp.Action.ActionTye.ADD_GOLD)){
      addLocalGold(amount);
    }else if(type===Number(rp.Action.ActionTye.ADD_DIAMOND)){
      var money=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo());
      money.diamond=Number(money.diamond||0)+amount;
      log("local diamond reward",amount,money.diamond);
    }else if(type===Number(rp.Action.ActionTye.ADD_CASH)){
      var cash=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo());
      cash.cash=Number(cash.cash||0)+amount;
      log("local cash reward",amount,cash.cash);
    }else if(type===Number(rp.Action.ActionTye.ADD_ITEM)){
      addLocalItem(p[0],p[1]);
    }else if(type===Number(rp.Action.ActionTye.ADD_PET)){
      localAddPetToStorage(u,p[0],p[1],0);
    }else if(type===Number(rp.Action.ActionTye.ADD_POINT_ITEM)){
      var pointId=Number(p[0])||0,pointAmount=Number(p[1])||0;
      var pointMoney=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo());
      if(pointId===1)pointMoney.cash=Number(pointMoney.cash||0)+pointAmount;
      else if(pointId===2)pointMoney.diamond=Number(pointMoney.diamond||0)+pointAmount;
      else if(pointId===3)pointMoney.gold=long(Number(pointMoney.gold||0)+pointAmount);
      else addLocalPointItem(pointId,pointAmount);
      log("local point currency reward",pointId,pointAmount);
    }else if(type===Number(rp.Action.ActionTye.ADD_LEVEL_EXP)){
      addLocalPointItem(p[0],p[1]);
    }else if(type===Number(rp.Action.ActionTye.UNLOCK_AVATAR)){
      var avatarId=Number(p[0])||0;
      if(avatarId>0){
        var bits=u.baseInfo.avatarBits;
        if(!Array.isArray(bits))bits=u.baseInfo.avatarBits=[];
        var bitIndex=Math.floor((avatarId-1)/32),bit=1<<((avatarId-1)%32);
        while(bits.length<=bitIndex)bits.push(0);
        bits[bitIndex]=(Number(bits[bitIndex])||0)|bit;
        log("local avatar unlocked",avatarId);
      }
    }else if(type>=100001&&type<=100015){
      localAddPetToStorage(u,p[0],p[1],type-100000);
    }
  }
  function localNormalizeRewardAction(raw){
    if(!raw)return null;
    var params=Array.isArray(raw.params)?raw.params:
      [raw.para1,raw.para2];
    return {type:Number(raw.type)||0,params:params};
  }
  function localUseSeed(id,serial){
    var userId=0;
    try{userId=Number(current&&current.baseInfo&&current.baseInfo.userId)||730001;}catch(_){}
    var a=(userId^Math.imul(Number(id)||0,2654435761)^Math.imul(Number(serial)||0,1013904223))>>>0;
    return (Math.imul(a,1664525)+1013904223)>>>0;
  }
  function localWeightedReward(rows,field,seed){
    var total=0;
    (rows||[]).forEach(function(row){total+=Math.max(0,Math.floor(Number(row&&row[field])||0));});
    if(total<=0)return null;
    var target=(Number(seed)>>>0)%total;
    for(var i=0;i<rows.length;i++){
      target-=Math.max(0,Math.floor(Number(rows[i]&&rows[i][field])||0));
      if(target<0)return rows[i];
    }
    return null;
  }
  function localGiftRewardActions(giftId,index,seed){
    var gift=null;
    try{gift=GC.G().GIFT_CONF.getDes(Number(giftId));}catch(_){}
    if(!gift||!Array.isArray(gift.awardNode)||!gift.awardNode.length)return null;
    var rows=gift.awardNode.slice(),picked=[];
    var kind=Number(gift.type);
    if(kind===3){
      picked=rows;
    }else if(kind===4){
      var selected=Number(index)||0;
      if(selected<1||selected>rows.length)return null;
      picked=[rows[selected-1]];
    }else if(kind===1){
      for(var i=0;i<rows.length;i++){
        var chance=Math.max(0,Math.min(10000,Number(rows[i].probValue)||0));
        if((localUseSeed(giftId,seed+i)%10000)<chance)picked.push(rows[i]);
      }
    }else if(kind===2||kind===5){
      var weighted=localWeightedReward(rows,"probValue",localUseSeed(giftId,seed));
      if(!weighted)return null;
      picked=[weighted];
    }else return null;
    return picked.map(localNormalizeRewardAction);
  }
  function localNewGiftRewardActions(giftId,index,seed,select){
    var rows=[];
    try{rows=GC.G().NEW_GIFT_CONF.getDesList().filter(function(x){return Number(x.giftId)===Number(giftId);});}catch(_){}
    if(!rows.length)return null;
    var row=null;
    if(select){
      var selected=Number(index)||0;
      if(selected<1||selected>rows.length)return null;
      row=rows[selected-1];
    }else row=localWeightedReward(rows,"percent",localUseSeed(giftId,seed));
    if(!row||!Array.isArray(row.actionArr))return null;
    return row.actionArr.map(localNormalizeRewardAction);
  }
  function localHangupItemReward(type,hours,u){
    hours=Math.max(0,Math.floor(Number(hours)||0));
    if(!hours)return null;
    var level=Math.max(1,Number(u&&u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneLevel)||1);
    var rows=[];
    try{rows=GC.G().HANGUP_CONF.getDesList();}catch(_){}
    var cfg=rows.find(function(x){
      return (Number(x.fromLevel)||0)<=level&&Number(x.toLevel)>=level;
    });
    if(!cfg)return null;
    if(Number(type)===Number(rp.Action.ActionTye.HANGUP_HOUR_GOLD))
      return {type:Number(rp.Action.ActionTye.ADD_GOLD),params:[Number(cfg.gold||0)*hours]};
    if(Number(type)===Number(rp.Action.ActionTye.HANGUP_HOUR_PET_EXP))
      return {type:Number(rp.Action.ActionTye.ADD_PET_EXP),params:[Number(cfg.petExp||0)*hours]};
    return null;
  }
  function localExpandUseActions(cfg,req,u,serial){
    var source=cfg&&cfg.actions;
    if(!Array.isArray(source)||!source.length)return null;
    var output=[],count=Math.max(1,Math.floor(Number(req&&req.count)||1));
    for(var unit=0;unit<count;unit++){
      for(var i=0;i<source.length;i++){
        var action=localNormalizeRewardAction(source[i]);
        if(!action)return null;
        var type=Number(action.type),params=action.params||[];
        if(type===Number(rp.Action.ActionTye.OPEN_GIFT_BOX)){
          var giftCount=Math.max(1,Math.floor(Number(params[1])||1));
          for(var g=0;g<giftCount;g++){
            var giftActions=localGiftRewardActions(params[0],req&&req.index,
              serial*97+unit*giftCount+g);
            if(!giftActions)return null;
            output=output.concat(giftActions);
          }
        }else if(type===Number(rp.Action.ActionTye.OPEN_NEW_GIFT_BOX)){
          var newGiftCount=Math.max(1,Math.floor(Number(params[1])||1));
          for(var ng=0;ng<newGiftCount;ng++){
            var newGiftActions=localNewGiftRewardActions(params[0],0,
              serial*131+unit*newGiftCount+ng,false);
            if(!newGiftActions)return null;
            output=output.concat(newGiftActions);
          }
        }else if(type===Number(rp.Action.ActionTye.HANGUP_HOUR_GOLD)||
                 type===Number(rp.Action.ActionTye.HANGUP_HOUR_PET_EXP)){
          var hangup=localHangupItemReward(type,params[0],u);
          if(!hangup)return null;
          output.push(hangup);
        }else output.push(action);
      }
    }
    return output;
  }
  function localValidateRewardPlan(u,actions){
    var petCount=0;
    for(var i=0;i<actions.length;i++){
      var a=actions[i],p=a&&a.params||[],type=Number(a&&a.type),id=Number(p[0])||0,n=Number(p[1])||0;
      if(type===Number(rp.Action.ActionTye.ADD_ITEM)){
        if(!id||n<=0||!localItemConfig(id))return false;
      }else if(type===Number(rp.Action.ActionTye.ADD_PET)){
        if(!id||n<=0)return false;
        try{if(!GC.G().spiritConfig.getDes(id))return false;}catch(_){return false;}
        petCount+=Math.floor(n);
      }else if(type>=100001&&type<=100015){
        if(!id||n<=0)return false;
        try{if(!GC.G().spiritConfig.getDes(id))return false;}catch(_){return false;}
        petCount+=Math.floor(n);
      }else if(type===Number(rp.Action.ActionTye.ADD_POINT_ITEM)){
        if(!id||n<=0)return false;
      }else if(type===Number(rp.Action.ActionTye.ADD_GOLD)||
               type===Number(rp.Action.ActionTye.ADD_EXP)||
               type===Number(rp.Action.ActionTye.ADD_DIAMOND)||
               type===Number(rp.Action.ActionTye.ADD_PET_EXP)||
               type===Number(rp.Action.ActionTye.ADD_CASH)||
               type===Number(rp.Action.ActionTye.ADD_LEVEL_EXP)){
        if(Number(p[0])<0)return false;
      }else if(type===Number(rp.Action.ActionTye.UNLOCK_AVATAR)){
        if(id<=0)return false;
      }else return false;
    }
    var storage=u&&u.petStorageInfo&&u.petStorageInfo.petArray||[];
    return storage.length+petCount<=100;
  }
  function localFindInventoryEntry(u,id,sid,count){
    if(!u||!u.itemPackInfo)return null;
    var pack=u.itemPackInfo,owners=localEquipmentOwners(u);
    sid=Number(sid)||0;
    if(sid){
      var selected=localItemBySid(u,sid);
      if(!selected||Number(selected.id)!==Number(id)||owners[String(selected.sid)])return null;
      return {kind:"sid",item:selected};
    }
    if(localEquipmentPosition(id)){
      var keys=Object.keys(pack.sidMap||{});
      for(var i=0;i<keys.length;i++){
        var item=pack.sidMap[keys[i]];
        if(item&&Number(item.id)===Number(id)&&!owners[String(item.sid)])return {kind:"sid",item:item};
      }
      return null;
    }
    var stack=pack.idMap&&pack.idMap[id];
    if(!stack||Number(stack.count||0)<count)return null;
    return {kind:"stack",item:stack};
  }
  function localConsumeInventoryEntry(u,entry,count){
    if(!u||!entry||!entry.item)return false;
    if(entry.kind==="sid"){
      if(count!==1)return false;
      var key=String(entry.item.sid);
      if(localEquipmentOwners(u)[key])return false;
      delete u.itemPackInfo.sidMap[key];
    }else{
      var item=entry.item;
      if(Number(item.count||0)<count)return false;
      item.count=Math.max(0,Number(item.count||0)-count);
      if(item.count===0)delete u.itemPackInfo.idMap[Number(item.id)];
    }
    refreshLocalItemIndexes(u);
    return true;
  }
  function localNotifyInventoryChanged(u,petChanged){
    try{
      var dm=typeof DM!=="undefined"&&DM.G&&DM.G();
      if(!dm)return;
      dm.userInfo=u;
      refreshLocalItemIndexes(u);
      try{
        var changeNotify=new rp.EntireNotify();
        changeNotify.userBaseInfo=u.baseInfo;
        changeNotify.itemPackInfo=[];
        changeNotify.petPackInfo=[];
        dm.onUserInfoChange(changeNotify);
      }catch(e){log("local base info notify",e);}
      var changes=[2];
      if(petChanged)changes.push(5);
      changes.forEach(function(type){
        dm.dataChangedFlag[type]=true;
        var handlers=dm.listeners&&dm.listeners[type]||[];
        handlers.slice().forEach(function(handler){
          try{if(handler&&handler.runWith)handler.runWith(changeNotify);else if(typeof handler==="function")handler(changeNotify);}catch(e){log("local inventory listener",type,e);}
        });
      });
    }catch(e){log("local inventory notify",e&&e.stack||e);}
  }
  function makeOfflineMixturePetRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;
    var ids=Array.isArray(req&&req.itemId)?req.itemId:[],
      requested=Array.isArray(req&&req.count)?req.count:[],
      plans=[],allActions=[],totalConsumed=0,seen={};
    if(!ids.length||ids.length>100){r.ret=1;return r;}
    var selectedGift=Number(window.__offlineSelectedGiftIndex)||0;
    for(var i=0;i<ids.length;i++){
      var id=Number(ids[i])||0,cfg=localItemConfig(id),
        stack=u.itemPackInfo&&u.itemPackInfo.idMap&&u.itemPackInfo.idMap[id],
        need=Math.max(1,Math.floor(Number(cfg&&cfg.composeNeedItemNum)||0)),
        available=Math.max(0,Math.floor(Number(stack&&stack.count)||0)),
        gain=Number(cfg&&cfg.composeGainId)||0,
        composeType=Number(cfg&&cfg.composeType),
        consume=Number(requested[i])>0?Math.floor(Number(requested[i])):Math.floor(available/need)*need;
      if(seen[id]||!cfg||!gain||!need||consume<need||consume>available||consume%need!==0){
        r.ret=1;log("local mixture rejected",id,available,need,consume);return r;
      }
      seen[id]=true;
      var outputCount=Math.floor(consume/need),actions=[];
      if(composeType===4){
        var legacy=localGiftRewardActions(gain,selectedGift,
          Number(offlineTaskMeta.itemUseCounter)||0);
        if(!legacy){r.ret=1;log("local mixture choice rejected",id,gain,selectedGift);return r;}
        for(var g=0;g<outputCount;g++)actions=actions.concat(legacy);
      }else if(composeType===5){
        var modern=localNewGiftRewardActions(gain,selectedGift,
          Number(offlineTaskMeta.itemUseCounter)||0,true);
        if(!modern){r.ret=1;log("local mixture new choice rejected",id,gain,selectedGift);return r;}
        for(var ng=0;ng<outputCount;ng++)actions=actions.concat(modern);
      }else{
        var rewardType=composeType===2?Number(rp.Action.ActionTye.ADD_PET):Number(rp.Action.ActionTye.ADD_ITEM);
        actions=[{type:rewardType,params:[gain,outputCount]}];
      }
      plans.push({id:id,consume:consume,actions:actions});
      allActions=allActions.concat(actions);totalConsumed+=consume;
    }
    // Validate every resulting item/pet before consuming any source fragments.
    if(!localValidateRewardPlan(u,allActions)){
      r.ret=1;log("local mixture reward validation failed");return r;
    }
    plans.forEach(function(entry){
      var item=u.itemPackInfo.idMap[entry.id];
      item.count=Math.max(0,Number(item.count||0)-entry.consume);
      if(item.count===0)delete u.itemPackInfo.idMap[entry.id];
      entry.actions.forEach(applyLocalRewardAction);
      log("local mixture composed",entry.id,entry.consume,entry.actions.length);
    });
    var petChanged=allActions.some(function(a){
      var type=Number(a&&a.type);
      return type===Number(rp.Action.ActionTye.ADD_PET)||
        (type>=100001&&type<=100015);
    });
    localNotifyInventoryChanged(u,petChanged);
    offlineTaskMeta.itemUseCounter=(Number(offlineTaskMeta.itemUseCounter)||0)+totalConsumed;
    window.__offlineSelectedGiftIndex=0;
    save();r.ret=0;
    log("local mixture batch complete",plans.length,totalConsumed);
    return r;
  }
  function localPetCrystalOwnedPets(u){
    var out=[],seen={};
    function add(p){
      if(!p||!Number(p.id)||!Number(p.genId))return;
      var key=String(p.genId);
      if(seen[key])return;
      seen[key]=true;out.push(p);
    }
    (u&&u.petPackInfo&&u.petPackInfo.packArray||[]).forEach(function(node){add(node&&node.pet);});
    (u&&u.petStorageInfo&&u.petStorageInfo.petArray||[]).forEach(add);
    return out;
  }
  function localPetStarLevelLimit(pet){
    var cfg=null,star=null;
    try{
      cfg=GC.G().spiritConfig.getDes(Number(pet&&pet.id));
      GC.G().PetStarConf.getDesList().some(function(x){
        if(cfg&&Number(x.templateId)===Number(cfg.starTemplateId)&&
           Number(x.star)===Number(pet&&pet.starLevel||cfg.quality)){
          star=x;return true;
        }
        return false;
      });
    }catch(e){log("local crystal star limit lookup",e);}
    return Math.max(1,Number(star&&star.levelLimit)||100);
  }
  function localRefreshPetCrystal(u){
    u=u||current;
    if(!u)return null;
    if(!u.petCrystalInfo)u.petCrystalInfo=new rp.PetCrystal();
    var info=u.petCrystalInfo;
    if(!info.slotInfo||typeof info.slotInfo!=="object")info.slotInfo={};
    if(!info.maxLevelGenIdMap||typeof info.maxLevelGenIdMap!=="object")info.maxLevelGenIdMap={};
    if(info.type!==1)info.type=0;
    var nowSeconds=Math.floor(Date.now()/1000);
    Object.keys(info.slotInfo).forEach(function(key){
      var slot=info.slotInfo[key];
      if(slot&&Number(slot.slotType)===Number(rp.PetCrystalSlot.Type.CoolDown)&&
         Number(slot.coolEndTime||0)<=nowSeconds){
        slot.slotType=Number(rp.PetCrystalSlot.Type.Unlock);
        slot.genId=0;slot.coolEndTime=0;
        log("local PetCrystal cooldown ended",Number(key));
      }
    });
    var pets=localPetCrystalOwnedPets(u).slice().sort(function(a,b){
      var la=Number(a.level)||1,lb=Number(b.level)||1;
      if(la!==lb)return lb-la;
      return (Number(b.fightScore)||0)-(Number(a.fightScore)||0);
    });
    var top=pets.slice(0,6);
    if(info.type===0){
      var map={};
      top.forEach(function(p){map[String(p.genId)]=Number(p.level)||1;});
      info.maxLevelGenIdMap=map;
      info.crystalLevel=top.length?Math.min.apply(null,top.map(function(p){return Number(p.level)||1;})):1;
      info.curCrystalLevel=info.crystalLevel;
      info.maxCrystalLevel=240;
    }else{
      // After breakthrough the six highest pets occupy the six free starter slots.
      info.maxLevelGenIdMap={};
      info.crystalLevel=Math.max(240,Number(info.crystalLevel)||240);
      info.curCrystalLevel=info.crystalLevel;
      var ancestors={};
      pets.forEach(function(p){
        if(Number(p.starLevel||0)<12)return;
        var cfg=null;try{cfg=GC.G().spiritConfig.getDes(Number(p.id));}catch(_){}
        var ancestor=Number(cfg&&cfg.ancestor)||Number(p.id);
        if(ancestor>0)ancestors[String(ancestor)]=true;
      });
      info.maxCrystalLevel=Math.min(500,240+Object.keys(ancestors).length*5);
    }
    return info;
  }
  function localCrystalFindPet(u,genId){
    genId=String(genId);
    var packs=u&&u.petPackInfo&&u.petPackInfo.packArray||[];
    for(var i=0;i<packs.length;i++){
      var p=packs[i]&&packs[i].pet;
      if(p&&String(p.genId)===genId)return p;
    }
    var stored=u&&u.petStorageInfo&&u.petStorageInfo.petArray||[];
    for(var j=0;j<stored.length;j++)if(stored[j]&&String(stored[j].genId)===genId)return stored[j];
    return null;
  }
  function localCrystalSyncPet(u,pet){
    if(!u||!pet)return;
    var packs=u.petPackInfo&&u.petPackInfo.packArray||[];
    packs.forEach(function(node){if(node&&node.pet&&String(node.pet.genId)===String(pet.genId))node.pet=pet;});
    var stored=u.petStorageInfo&&u.petStorageInfo.petArray||[];
    stored.forEach(function(entry){if(entry&&String(entry.genId)===String(pet.genId))Object.keys(pet).forEach(function(k){entry[k]=pet[k];});});
  }
function localPetOwnedRecord(u,genId){
    genId=String(genId);
    var packs=u&&u.petPackInfo&&u.petPackInfo.packArray||[];
    for(var i=0;i<packs.length;i++){
      var node=packs[i],pet=node&&node.pet;
      if(pet&&String(pet.genId)===genId)return {kind:"pack",index:i,node:node,pet:pet};
    }
    var stored=u&&u.petStorageInfo&&u.petStorageInfo.petArray||[];
    for(var j=0;j<stored.length;j++){
      if(stored[j]&&String(stored[j].genId)===genId)
        return {kind:"storage",index:j,pet:stored[j]};
    }
    return null;
  }
  function localPetStarCostMatches(target,targetCfg,candidate,rule){
    if(!target||!targetCfg||!candidate||!rule)return false;
    if(Number(candidate.starLevel||0)!==Number(rule.star||0))return false;
    var cfg=null;
    try{cfg=GC.G().spiritConfig.getDes(Number(candidate.id));}catch(_){}
    if(!cfg)return false;
    // Match the archived selection panel: star level plus any configured
    // same-element, same-pet, or ancestor requirement. Do not add extra rules.
    if(Number(rule.sameElement||0)&&Number(cfg.element)!==Number(targetCfg.element))
      return false;
    if(Number(rule.samePet||0)){
      var ancestor=Number(targetCfg.ancestor)||Number(targetCfg.evoAncestor)||Number(target.id);
      if(Number(candidate.id)!==ancestor)return false;
    }
    if(Number(rule.petId||0)>0&&Number(cfg.ancestor||cfg.id)!==Number(rule.petId))
      return false;
    return true;
  }
  function localRemovePetForStarUp(u,genId){
    var record=localPetOwnedRecord(u,genId);
    if(!record)return false;
    if(record.kind==="pack"){
      var node=record.node;
      if((node.equip||[]).length)return false;
      node.pet=null;node.state=0;node.combatPos=0;
    }else{
      u.petStorageInfo.petArray.splice(record.index,1);
    }
    return true;
  }
  function localPetStarLevelUp(u,targetGenId,groups){
    if(!u||!u.baseInfo||!Number(targetGenId))return {ok:false,reason:"missing user or target"};
    var targetRecord=localPetOwnedRecord(u,targetGenId);
    if(!targetRecord)return {ok:false,reason:"target pet not owned"};
    var target=targetRecord.pet,targetCfg=null;
    try{targetCfg=GC.G().spiritConfig.getDes(Number(target.id));}catch(_){}
    if(!targetCfg)return {ok:false,reason:"target pet config missing"};
    var currentStar=Math.max(1,Number(target.starLevel)||1);
    var nextStar=currentStar+1;
    var maxConfiguredStar=0;
    try{
      (GC.G().PetStarConf.getDesList()||[]).forEach(function(row){
        if(Number(row.templateId)===Number(targetCfg.starTemplateId))
          maxConfiguredStar=Math.max(maxConfiguredStar,Number(row.star)||0);
      });
    }catch(_){}
    if(!maxConfiguredStar||nextStar>maxConfiguredStar)
      return {ok:false,reason:"maximum configured star reached"};
    var starCfg=null;
    try{starCfg=GC.G().PetStarConf.getDes(Number(targetCfg.starTemplateId)*100+nextStar);}catch(_){}
    if(!starCfg||Number(starCfg.star)!==nextStar)
      return {ok:false,reason:"next star configuration missing"};
    var rules=Array.isArray(starCfg.cost)?starCfg.cost:[];
    groups=Array.isArray(groups)?groups:[];
    if(groups.length!==rules.length)return {ok:false,reason:"star cost groups mismatch"};
    var selected=[],seen={},allActions=[],cardTotals={};
    var startupCardIds={
      5:[1001163,1001160,1001159,1001162,1001161],
      6:[1001169,1001166,1001165,1001168,1001167],
      9:[1001174,1001171,1001170,1001173,1001172],
      10:[1001179,1001176,1001175,1001178,1001177],
      11:[1001339,1001340,1001341,1001342,1001343],
      12:[1001344,1001345,1001346,1001347,1001348],
      13:[1001349,1001350,1001351,1001352,1001353],
      14:[1001354,1001355,1001356,1001357,1001358],
      15:[1001359,1001360,1001361,1001362,1001363]
    };
    for(var g=0;g<rules.length;g++){
      var rule=rules[g]||{},group=groups[g]||{},
        ids=Array.isArray(group)?group:(Array.isArray(group.petGenIds)?group.petGenIds:[]),
        cards=Array.isArray(group.costCards)?group.costCards:[];
      var cardCount=0,allowedCards=startupCardIds[Number(rule.star)]||[];
      if(Number(rule.samePet||0))allowedCards=[];
      else if(Number(rule.sameElement||0)){
        var elementIndex=Number(targetCfg.element)-1;
        allowedCards=elementIndex>=0&&elementIndex<allowedCards.length?[allowedCards[elementIndex]]:[];
      }
      for(var c=0;c<cards.length;c++){
        var card=cards[c]||{},cardId=Number(card.itemId)||0,count=Math.floor(Number(card.count)||0);
        if(!cardId||count<=0||allowedCards.indexOf(cardId)<0)
          return {ok:false,reason:"invalid star soul card for configured cost"};
        cardCount+=count;cardTotals[cardId]=(cardTotals[cardId]||0)+count;
      }
      if(ids.length+cardCount!==Number(rule.num||0))
        return {ok:false,reason:"wrong fodder pet/card count"};
      for(var k=0;k<ids.length;k++){
        var id=Number(ids[k])||0,key=String(id),record=localPetOwnedRecord(u,id);
        if(!id||id===Number(targetGenId)||seen[key]||!record)
          return {ok:false,reason:"fodder pet missing or duplicated"};
        if(!localPetStarCostMatches(target,targetCfg,record.pet,rule))
          return {ok:false,reason:"fodder pet does not match configured star cost"};
        if(record.kind==="pack"&&(record.node.equip||[]).length)
          return {ok:false,reason:"fodder pet still has equipment"};
        seen[key]=true;selected.push(id);
      }
    }
    var costActions=starCfg.actionArr;
    if(costActions){
      if(Array.isArray(costActions))allActions=costActions.map(localNormalizeRewardAction);
      else allActions=[localNormalizeRewardAction(costActions)];
      if(allActions.some(function(x){return !x;}))
        return {ok:false,reason:"invalid star-up cost action"};
    }
    Object.keys(cardTotals).forEach(function(id){
      allActions.push(localNormalizeRewardAction({
        type:Number(rp.Action.ActionTye.DEL_ITEM_BY_ID),
        params:[Number(id),Number(cardTotals[id])]
      }));
    });
    var oldStarCfg=null;
    try{oldStarCfg=GC.G().PetStarConf.getDes(Number(targetCfg.starTemplateId)*100+currentStar);}catch(_){}
    function effectFor(row,type){
      var result={percentValue:0,value:0};
      (row&&row.effectInfo||[]).forEach(function(effect){
        if(Number(effect.effectType)!==type)return;
        if(Number(effect.percentValue)>0)result.percentValue=Number(effect.percentValue);
        if(Number(effect.value)>0)result.value=Number(effect.value);
      });
      return result;
    }
    function nextStarStat(oldValue,type){
      var before=effectFor(oldStarCfg,type),after=effectFor(starCfg,type),
        percentDelta=after.percentValue-before.percentValue,
        valueDelta=after.value-before.value,
        starValueDelta=(Number(starCfg.starAddVal)||0)-(Number(oldStarCfg&&oldStarCfg.starAddVal)||0);
      return Math.round(Number(oldValue||0)*(1+starValueDelta/10000)*
        (1+percentDelta/10000)+valueDelta);
    }
    var upgradedStats={
      hp:nextStarStat(target.hp,12),
      attack:nextStarStat(target.attack,13),
      defense:nextStarStat(target.defense,14)
    };
    if(upgradedStats.hp<=0||upgradedStats.attack<=0||upgradedStats.defense<0)
      return {ok:false,reason:"invalid star-up attributes"};
    var oldHp=Number(target.hp)||0,oldAttack=Number(target.attack)||0,oldDefense=Number(target.defense)||0;
    var newFightScore=Math.floor((Number(target.fightScore)||0)+
      1.1*(upgradedStats.hp-oldHp)+10*(upgradedStats.attack-oldAttack)+
      10*(upgradedStats.defense-oldDefense));
    var costPlan=localCrystalCostInfo(u,allActions);
    if(!costPlan.ok)return {ok:false,reason:"star-up materials insufficient"};
    try{
      if(!localCrystalConsumeCosts(u,costPlan.requirements))
        return {ok:false,reason:"star-up cost could not be consumed"};
    }catch(e){
      return {ok:false,reason:"star-up cost error: "+String(e&&e.message||e)};
    }
    for(var n=0;n<selected.length;n++){
      if(!localRemovePetForStarUp(u,selected[n]))
        return {ok:false,reason:"fodder pet removal failed"};
    }
    target.starLevel=nextStar;
    target.levelLimit=Number(starCfg.levelLimit)||Number(target.levelLimit)||100;
    target.hp=long(upgradedStats.hp);target.attack=long(upgradedStats.attack);
    target.defense=long(upgradedStats.defense);target.fightScore=long(newFightScore);
    localCrystalSyncPet(u,target);
    localNotifyInventoryChanged(u,true);
    save();
    log("local pet star-up",Number(target.id),String(targetGenId),currentStar,"->",nextStar,
      "fodder",selected.join(","),"cards",JSON.stringify(cardTotals),"materials",allActions.length,
      "stats",String(target.hp),String(target.attack),String(target.defense),String(target.fightScore));
    return {ok:true,target:target,star:nextStar,consumedPets:selected,starConfig:starCfg};
  }
  function makeOfflinePetStarLevelUpRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    var targets=Array.isArray(req&&req.petGenIds)?req.petGenIds.map(function(x){return Number(x)||0;}):[];
    var rawGroups=Array.isArray(req&&req.costGroups)?req.costGroups:[];
    if(!u||!u.baseInfo||!targets.length||rawGroups.length!==targets.length){
      r.ret=1;log("local PetStarLevelUp rejected: invalid targets or cost groups");return r;
    }
    var targetSet={},fodderSet={},plans=[],allActions=[];
    for(var t=0;t<targets.length;t++){
      var targetId=targets[t],targetKey=String(targetId);
      if(!targetId||targetSet[targetKey]){
        r.ret=1;log("local PetStarLevelUp rejected: duplicate target",targetKey);return r;
      }
      targetSet[targetKey]=true;
    }
    for(var t=0;t<targets.length;t++){
      var targetId=targets[t],targetRecord=localPetOwnedRecord(u,targetId);
      if(!targetRecord){
        r.ret=1;log("local PetStarLevelUp rejected: target not owned",targetId);return r;
      }
      var target=targetRecord.pet,targetCfg=null,starCfg=null;
      try{
        targetCfg=GC.G().spiritConfig.getDes(Number(target.id));
        if(targetCfg)starCfg=GC.G().PetStarConf.getDes(
          Number(targetCfg.starTemplateId)*100+Math.max(1,Number(target.starLevel)||1)+1
        );
      }catch(e){log("local PetStarLevelUp config lookup",e&&e.stack||e);}
      if(!targetCfg||!starCfg){
        r.ret=1;log("local PetStarLevelUp rejected: target star config missing",targetId);return r;
      }
      var rules=Array.isArray(starCfg.cost)?starCfg.cost:[],
        raw=rawGroups[t]||{},
        flatIds=Array.isArray(raw.costPetGenIds)?raw.costPetGenIds.map(function(x){return Number(x)||0;}):[],
        expected=rules.reduce(function(sum,rule){return sum+Math.max(0,Math.floor(Number(rule&&rule.num)||0));},0);
      if(flatIds.length!==expected){
        r.ret=1;log("local PetStarLevelUp rejected: wrong fodder count",targetId,flatIds.length,expected);return r;
      }
      var groups=[],cursor=0;
      for(var g=0;g<rules.length;g++){
        var rule=rules[g]||{},count=Math.max(0,Math.floor(Number(rule.num)||0)),
          ids=flatIds.slice(cursor,cursor+count);
        cursor+=count;
        for(var k=0;k<ids.length;k++){
          var fodderId=ids[k],fodderKey=String(fodderId);
          if(!fodderId||targetSet[fodderKey]||fodderSet[fodderKey]){
            r.ret=1;log("local PetStarLevelUp rejected: invalid or reused fodder",targetId,fodderKey);return r;
          }
          var fodder=localPetOwnedRecord(u,fodderId);
          if(!fodder||!localPetStarCostMatches(target,targetCfg,fodder.pet,rule)){
            r.ret=1;log("local PetStarLevelUp rejected: fodder does not match cost",targetId,fodderKey);return r;
          }
          if(fodder.kind==="pack"&&(fodder.node.equip||[]).length){
            r.ret=1;log("local PetStarLevelUp rejected: fodder has equipment",targetId,fodderKey);return r;
          }
          fodderSet[fodderKey]=true;
        }
        groups.push({petGenIds:ids,costCards:[]});
      }
      var costActions=starCfg.actionArr;
      if(costActions){
        var normalized=Array.isArray(costActions)?
          costActions.map(localNormalizeRewardAction):
          [localNormalizeRewardAction(costActions)];
        if(normalized.some(function(action){return !action;})){
          r.ret=1;log("local PetStarLevelUp rejected: invalid cost action",targetId);return r;
        }
        allActions=allActions.concat(normalized);
      }
      plans.push({targetId:targetId,groups:groups});
    }
    var totalCost=localCrystalCostInfo(u,allActions);
    if(!totalCost.ok){
      r.ret=1;log("local PetStarLevelUp rejected: insufficient batch materials");return r;
    }
    for(var p=0;p<plans.length;p++){
      var result=localPetStarLevelUp(u,plans[p].targetId,plans[p].groups);
      if(!result.ok){
        r.ret=1;log("local PetStarLevelUp batch stopped",plans[p].targetId,result.reason);return r;
      }
    }
    r.ret=0;
    log("local PetStarLevelUp batch PASS",targets.length);
    return r;
  }
  function makeOfflineOnePetStarLevelUpRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    var choices=Array.isArray(req&&req.choiceCost)?req.choiceCost:[],groups=[];
    for(var i=0;i<choices.length;i++){
      var choice=choices[i]||{};
      groups.push({petGenIds:choice.petGenIds||[],costCards:choice.costCards||[]});
    }
    var result=localPetStarLevelUp(u,req&&req.petGenIds,groups);
    r.ret=result.ok?0:1;
    if(result.ok)r.petGenId=Number(req.petGenIds);
    else log("local OnePetStarLevelUp rejected",Number(req&&req.petGenIds),result.reason);
    return r;
  }
          function localCrystalCostInfo(u,actions){
    var money=u&&u.baseInfo&&u.baseInfo.moneyInfo||new rp.MoneyInfo();
    var points=u&&u.baseInfo&&u.baseInfo.newPointItemMap||{};
    var requirements={items:{},gold:0,diamond:0,cash:0,points:{}};
    (actions||[]).forEach(function(a){
      var type=Number(a&&a.type),p=a&&a.params||[a&&a.para1,a&&a.para2],
        id=Number(p[0])||0,n=Number(p[1])||0;
      if(type===Number(rp.Action.ActionTye.ADD_GOLD))requirements.gold+=id;
      else if(type===Number(rp.Action.ActionTye.ADD_DIAMOND))requirements.diamond+=id;
      else if(type===Number(rp.Action.ActionTye.ADD_CASH))requirements.cash+=id;
      else if(type===Number(rp.Action.ActionTye.ADD_POINT_ITEM)){
        if(id===1)requirements.cash+=n;
        else if(id===2)requirements.diamond+=n;
        else if(id===3)requirements.gold+=n;
        else requirements.points[id]=(requirements.points[id]||0)+n;
      }else if(type===Number(rp.Action.ActionTye.DEL_ITEM_BY_ID)){
        requirements.items[id]=(requirements.items[id]||0)+n;
      }else{
        requirements.invalid=true;
      }
    });
    var ok=Number(money.gold||0)>=requirements.gold&&
      Number(money.diamond||0)>=requirements.diamond&&
      Number(money.cash||0)>=requirements.cash;
    Object.keys(requirements.points).forEach(function(id){
      if(Number(points[id]||0)<requirements.points[id])ok=false;
    });
    Object.keys(requirements.items).forEach(function(id){
      var item=u.itemPackInfo&&u.itemPackInfo.idMap&&u.itemPackInfo.idMap[id];
      if(Number(item&&item.count||0)<requirements.items[id])ok=false;
    });
    if(requirements.invalid)ok=false;
    return {ok:ok,requirements:requirements};
  }
  function localCrystalConsumeCosts(u,requirements){
    if(!u||!u.baseInfo||!requirements)return false;
    var money=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo());
    var points=u.baseInfo.newPointItemMap||(u.baseInfo.newPointItemMap={});
    var r=requirements;
    if(Number(money.gold||0)<r.gold||Number(money.diamond||0)<r.diamond||Number(money.cash||0)<r.cash)return false;
    Object.keys(r.points||{}).forEach(function(id){
      if(Number(points[id]||0)<r.points[id])throw new Error("not enough point item "+id);
    });
    Object.keys(r.items||{}).forEach(function(id){
      var item=u.itemPackInfo&&u.itemPackInfo.idMap&&u.itemPackInfo.idMap[id];
      if(Number(item&&item.count||0)<r.items[id])throw new Error("not enough item "+id);
    });
    money.gold=long(Number(money.gold||0)-r.gold);
    money.diamond=Number(money.diamond||0)-r.diamond;
    money.cash=Number(money.cash||0)-r.cash;
    Object.keys(r.points||{}).forEach(function(id){points[id]=Number(points[id]||0)-r.points[id];});
    Object.keys(r.items||{}).forEach(function(id){
      var item=u.itemPackInfo.idMap[id];
      item.count=Number(item.count||0)-r.items[id];
      if(item.count<=0)delete u.itemPackInfo.idMap[id];
    });
    refreshLocalItemIndexes(u);
    return true;
  }
  function localCrystalMaxLevel(u){
    var ancestors={};
    localPetCrystalOwnedPets(u).forEach(function(p){
      if(Number(p.starLevel||0)<12)return;
      var cfg=null;try{cfg=GC.G().spiritConfig.getDes(Number(p.id));}catch(_){}
      var ancestor=Number(cfg&&cfg.ancestor)||Number(p.id);
      if(ancestor>0)ancestors[String(ancestor)]=true;
    });
    return Math.min(500,240+Object.keys(ancestors).length*5);
  }
  function makeOfflinePetCrystalInfoRsp(r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;r.ret=0;r.info=localRefreshPetCrystal(u);
    log("local PetCrystalInfoRsp",r.info.type,r.info.crystalLevel,
      r.info.maxCrystalLevel,Object.keys(r.info.slotInfo||{}).length);
    return r;
  }
  function makeOfflinePetCrystalSetRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;var info=localRefreshPetCrystal(u),index=Number(req&&req.index),
      genId=Number(req&&req.genId)||0,slot=info&&info.slotInfo&&info.slotInfo[index],
      pet=genId&&localCrystalFindPet(u,genId);
    if(!info||!Number.isInteger(index)||index<1||index>60||!slot||
       Number(slot.slotType)!==Number(rp.PetCrystalSlot.Type.Unlock)||!pet){
      r.ret=1;log("local PetCrystalSet rejected",index,genId,slot&&slot.slotType);return r;
    }
    var duplicate=false;
    Object.keys(info.slotInfo).forEach(function(key){
      if(Number(key)!==index&&info.slotInfo[key]&&Number(info.slotInfo[key].genId)===genId)duplicate=true;
    });
    if(duplicate){r.ret=1;log("local PetCrystalSet duplicate pet",genId);return r;}
    slot.slotType=Number(rp.PetCrystalSlot.Type.Used);slot.genId=genId;slot.coolEndTime=0;
    var maxLevel=localPetStarLevelLimit(pet);
    pet.crystalLevel=Math.min(Number(info.crystalLevel)||1,maxLevel);
    localCrystalSyncPet(u,pet);
    r.ret=0;r.info=info;
    localNotifyInventoryChanged(u,false);save();
    log("local PetCrystalSet",index,genId,"crystalLevel",pet.crystalLevel);
    return r;
  }
  function makeOfflinePetCrystalGetRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;var info=localRefreshPetCrystal(u),index=Number(req&&req.index),
      slot=info&&info.slotInfo&&info.slotInfo[index];
    if(!info||!Number.isInteger(index)||!slot||Number(slot.slotType)!==Number(rp.PetCrystalSlot.Type.Used)){
      r.ret=1;log("local PetCrystalGet rejected",index,slot&&slot.slotType);return r;
    }
    var pet=localCrystalFindPet(u,slot.genId);
    if(pet){pet.crystalLevel=0;localCrystalSyncPet(u,pet);}
    // The archived pet-crystal flow uses an eight-hour cooldown.
    var cooldownSeconds=8*60*60;
    slot.slotType=Number(rp.PetCrystalSlot.Type.CoolDown);
    slot.coolEndTime=Math.floor(Date.now()/1000)+cooldownSeconds;
    r.ret=0;r.info=info;
    localNotifyInventoryChanged(u,false);save();
    log("local PetCrystalGet",index,Number(pet&&pet.genId)||0,
      "cooldown",cooldownSeconds,"until",slot.coolEndTime);
    return r;
  }
  function makeOfflinePetCrystalUnlockRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;var info=localRefreshPetCrystal(u),index=Number(req&&req.index),
      costType=Number(req&&req.costType),cfg=null,slot=info&&info.slotInfo&&info.slotInfo[index];
    if(!info||!Number.isInteger(index)||index<7||index>60||!isFinite(costType)||
       costType<0||costType>1||(slot&&Number(slot.slotType)>0)){
      r.ret=1;log("local PetCrystalUnlock rejected",index,costType);return r;
    }
    try{cfg=GC.G().PET_CRYSTAL_SLOT.getDes(index);}catch(_){}
    var actions=cfg&&cfg.actionArr||[],action=actions[costType];
    if(!action){r.ret=1;log("local PetCrystalUnlock config missing",index,costType);return r;}
    var plan=localCrystalCostInfo(u,[localNormalizeRewardAction(action)]);
    if(!plan.ok){r.ret=1;log("local PetCrystalUnlock cost missing",index,costType);return r;}
    try{localCrystalConsumeCosts(u,plan.requirements);}catch(e){r.ret=1;log("local PetCrystalUnlock cost error",e);return r;}
    info.slotInfo[index]=new rp.PetCrystalSlot();
    info.slotInfo[index].slotType=Number(rp.PetCrystalSlot.Type.Unlock);
    info.slotInfo[index].genId=0;info.slotInfo[index].coolEndTime=0;
    r.ret=0;r.info=info;
    localNotifyInventoryChanged(u,false);save();
    log("local PetCrystalUnlock",index,costType);
    return r;
  }
  function makeOfflinePetCrystalBuyCoolTimeRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;var info=localRefreshPetCrystal(u),index=Number(req&&req.index),
      slot=info&&info.slotInfo&&info.slotInfo[index],now=Math.floor(Date.now()/1000);
    if(!info||!slot||Number(slot.slotType)!==Number(rp.PetCrystalSlot.Type.CoolDown)){
      r.ret=1;return r;
    }
    var cost=Math.ceil(Math.max(0,Number(slot.coolEndTime||0)-now)/300),
      money=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo());
    if(Number(money.cash||0)<cost){r.ret=1;log("local PetCrystalBuyCoolTime missing cash",cost);return r;}
    money.cash=Number(money.cash||0)-cost;
    slot.slotType=Number(rp.PetCrystalSlot.Type.Unlock);slot.coolEndTime=0;slot.genId=0;
    r.ret=0;r.info=info;localNotifyInventoryChanged(u,false);save();
    log("local PetCrystalBuyCoolTime",index,cost);
    return r;
  }
  function makeOfflinePetCrystalBreakRsp(r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;var info=localRefreshPetCrystal(u);
    if(info.type===0){
      var top=localPetCrystalOwnedPets(u).slice().sort(function(a,b){return (Number(b.level)||1)-(Number(a.level)||1);}).slice(0,6);
      var minLevel=top.length>=6?Math.min.apply(null,top.map(function(p){return Number(p.level)||1;})):0;
      if(top.length<6||minLevel<240){
        r.ret=1;log("local PetCrystalBreak blocked",top.length,minLevel);return r;
      }
      info.type=1;info.crystalLevel=240;info.curCrystalLevel=240;
      info.maxCrystalLevel=localCrystalMaxLevel(u);
      if(info.maxCrystalLevel<240)info.maxCrystalLevel=240;
      info.maxLevelGenIdMap={};
      top.forEach(function(p,index){
        var slot=new rp.PetCrystalSlot();
        slot.slotType=Number(rp.PetCrystalSlot.Type.Used);
        slot.genId=Number(p.genId);slot.coolEndTime=0;
        info.slotInfo[index+1]=slot;
        p.crystalLevel=Math.min(240,localPetStarLevelLimit(p));
        localCrystalSyncPet(u,p);
      });
      log("local PetCrystalBreak unlocked",info.crystalLevel,info.maxCrystalLevel);
    }else{
      var level=Number(info.crystalLevel)||240,
        max=localCrystalMaxLevel(u),cfg=null;
      info.maxCrystalLevel=Math.max(240,max);
      if(level>=info.maxCrystalLevel){r.ret=1;log("local PetCrystalBreak max level",level,info.maxCrystalLevel);return r;}
      try{cfg=GC.G().PET_CRYSTAL_LEVEL_UP.getDes(level);}catch(_){}
      if(!cfg||!Array.isArray(cfg.actionArr)){r.ret=1;log("local PetCrystalBreak config missing",level);return r;}
      var plan=localCrystalCostInfo(u,cfg.actionArr);
      if(!plan.ok){r.ret=1;log("local PetCrystalBreak cost missing",level);return r;}
      try{localCrystalConsumeCosts(u,plan.requirements);}catch(e){r.ret=1;log("local PetCrystalBreak cost error",e);return r;}
      info.crystalLevel=level+1;info.curCrystalLevel=level+1;
      log("local PetCrystalBreak level up",level,"->",info.crystalLevel);
    }
    r.ret=0;r.info=info;
    localNotifyInventoryChanged(u,false);save();
    return r;
  }
    function makeOfflineUseItemRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;normalizeLocalEquipmentInventory(u);
    var id=Number(req&&req.id)||0,kind=Number(req&&req.useType),
      count=Math.floor(Number(req&&req.count)||1),sid=Number(req&&req.sid)||0;
    if(!id||count<1||count>999||[1,2,3,4].indexOf(kind)<0){r.ret=1;return r;}
    var cfg=localItemConfig(id);
    if(!cfg){r.ret=1;log("local item operation rejected: config missing",id,kind);return r;}
    var entry=localFindInventoryEntry(u,id,sid,count);
    if(!entry){r.ret=1;log("local item operation rejected: insufficient or equipped",id,sid,count,kind);return r;}
    if(entry.kind==="sid"&&count!==1){r.ret=1;return r;}
    var plan=[],units=0;
    if(kind===Number(rp.UseItemReq.UseType.USETYPE_SELL)){
      var sell=cfg.sellNode;
      var sellPointId=({1:3,2:2,3:1})[Number(sell&&sell.moneyType)];
      if(!sellPointId||Number(sell.moneyNum)<=0){r.ret=1;return r;}
      plan=[{type:Number(rp.Action.ActionTye.ADD_POINT_ITEM),params:[
        sellPointId,Number(sell.moneyNum)*count]}];
      units=count;
    }else if(kind===Number(rp.UseItemReq.UseType.USETYPE_DECOMPOSE)){
      var decomposed=cfg.decomposeGain;
      if(!decomposed||Number(decomposed.itemId)<=0||Number(decomposed.itemNum)<=0){r.ret=1;return r;}
      plan=[{type:Number(rp.Action.ActionTye.ADD_ITEM),params:[
        Number(decomposed.itemId),Number(decomposed.itemNum)*count]}];
      units=count;
    }else if(kind===Number(rp.UseItemReq.UseType.USETYPE_COMPOSE)){
      var need=Math.max(1,Math.floor(Number(cfg.composeNeedItemNum)||0));
      var outputCount=Math.floor(count/need),composeType=Number(cfg.composeType),gain=Number(cfg.composeGainId)||0;
      if(!cfg.composeNeedItemNum||outputCount<1||outputCount*need!==count||!gain){r.ret=1;return r;}
      if(composeType===1||composeType===3){
        plan=[{type:Number(rp.Action.ActionTye.ADD_ITEM),params:[gain,outputCount]}];
      }else if(composeType===2){
        plan=[{type:Number(rp.Action.ActionTye.ADD_PET),params:[gain,outputCount]}];
      }else if(composeType===4){
        var giftActions=localGiftRewardActions(gain,req&&req.index,
          Number(offlineTaskMeta.itemUseCounter)||0);
        if(!giftActions){r.ret=1;log("local compose legacy gift rejected: choose a valid reward",id,gain,req&&req.index);return r;}
        for(var out=0;out<outputCount;out++)plan=plan.concat(giftActions);
      }else if(composeType===5){
        var newGiftActions=localNewGiftRewardActions(gain,req&&req.index,
          Number(offlineTaskMeta.itemUseCounter)||0,true);
        if(!newGiftActions){r.ret=1;log("local compose new gift rejected: choose a valid reward",id,gain,req&&req.index);return r;}
        for(var newOut=0;newOut<outputCount;newOut++)plan=plan.concat(newGiftActions);
      }else{r.ret=1;return r;}
      units=outputCount;
    }else if(kind===Number(rp.UseItemReq.UseType.USETYPE_USE)){
      plan=localExpandUseActions(cfg,req,u,Number(offlineTaskMeta.itemUseCounter)||0);
      if(!plan){r.ret=1;log("local item use rejected: unsupported action",id);return r;}
      units=count;
    }
    if(!localValidateRewardPlan(u,plan)){
      r.ret=1;log("local item operation rejected: reward cannot be represented locally",id,kind);
      return r;
    }
    if(!localConsumeInventoryEntry(u,entry,count)){
      r.ret=1;log("local item operation rejected during consume",id,count);
      return r;
    }
    plan.forEach(function(action){applyLocalRewardAction(action);});
    offlineTaskMeta.itemUseCounter=(Number(offlineTaskMeta.itemUseCounter)||0)+Math.max(1,units);
    localNotifyInventoryChanged(u,plan.some(function(a){
      return Number(a.type)===Number(rp.Action.ActionTye.ADD_PET)||
        (Number(a.type)>=100001&&Number(a.type)<=100015);
    }));
    save();
    r.ret=0;
    log("local item operation",id,kind,"count",count,"rewards",plan.length);
    return r;
  }
  function localPetLevelCostAvailable(u,cfg){
    var actions=cfg&&cfg.actionArr||[],money=u.baseInfo.moneyInfo||new rp.MoneyInfo(),points=u.baseInfo.newPointItemMap||{};
    for(var i=0;i<actions.length;i++){
      var a=actions[i]||{},type=Number(a.type),id=Number(a.para1)||0,count=Number(a.para2)||0;
      if(type===Number(rp.Action.ActionTye.ADD_GOLD)&&Number(money.gold||0)<id)return false;
      if(type===Number(rp.Action.ActionTye.ADD_POINT_ITEM)&&(Number(points[id])||0)<count)return false;
      if(type===Number(rp.Action.ActionTye.ADD_ITEM)){
        var item=u.itemPackInfo&&u.itemPackInfo.idMap&&u.itemPackInfo.idMap[id];
        if(Number(item&&item.count||0)<count)return false;
      }
    }
    return true;
  }
  function consumeLocalPetLevelCost(u,cfg){
    var actions=cfg&&cfg.actionArr||[],money=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo());
    var points=u.baseInfo.newPointItemMap||(u.baseInfo.newPointItemMap={});
    for(var i=0;i<actions.length;i++){
      var a=actions[i]||{},type=Number(a.type),id=Number(a.para1)||0,count=Number(a.para2)||0;
      if(type===Number(rp.Action.ActionTye.ADD_GOLD))money.gold=long(Math.max(0,Number(money.gold||0)-id));
      else if(type===Number(rp.Action.ActionTye.ADD_POINT_ITEM))points[id]=Math.max(0,(Number(points[id])||0)-count);
      else if(type===Number(rp.Action.ActionTye.ADD_ITEM)){
        var item=u.itemPackInfo.idMap[id];item.count=Math.max(0,(Number(item.count)||0)-count);
      }
    }
  }
function makeOfflinePetGrowupEvolveRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;
    var index=Number(req&&req.index),packs=normalizePetPack(u);
    if(!Number.isInteger(index)||index<0||index>=18||!packs[index]||!packs[index].pet){
      r.ret=1;log("local PetGrowupEvolve rejected: invalid pack index",index);return r;
    }
    var pet=packs[index].pet,parentCfg=null,childCfg=null,evolveCfg=null;
    try{
      parentCfg=GC.G().spiritConfig.getDes(Number(pet.id));
      var childId=Number(parentCfg&&parentCfg.evoChild)||Number(parentCfg&&parentCfg.child)||0;
      childCfg=childId&&GC.G().spiritConfig.getDes(childId);
      // Archived spirit rows store their evolution tier as starLevel;
      // the original UI reads the matching evolution row by this tier.
      var quality=Number(parentCfg&&parentCfg.quality)||Number(parentCfg&&parentCfg.starLevel)||0;
      evolveCfg=GC.G().evolutionConfig.getDes(quality);
    }catch(e){log("local evolution config lookup",e&&e.stack||e);}
    if(!parentCfg||!childId||!childCfg||!Number(childCfg.id)||!evolveCfg){
      r.ret=1;log("local PetGrowupEvolve blocked: no child form/config",Number(pet.id));return r;
    }
    var oldLevel=Math.max(1,Number(pet.level)||1);
    var itemId=Number(evolveCfg.itemId)||0,itemCount=Math.max(0,Math.floor(Number(evolveCfg.itemCount)||0)),
      coinCount=Math.max(0,Math.floor(Number(evolveCfg.coinCount)||0)),
      inventory=u.itemPackInfo&&u.itemPackInfo.idMap&&u.itemPackInfo.idMap[itemId],
      money=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo());
    if(!itemId||!itemCount||Number(inventory&&inventory.count||0)<itemCount||
       Number(money.gold||0)<coinCount){
      r.ret=1;log("local PetGrowupEvolve blocked: insufficient cost",itemId,itemCount,
        Number(inventory&&inventory.count||0),coinCount,String(money.gold||0));return r;
    }
    var starDes=null,starBonus=0,insightCfg=null;
    try{
      // The original evolution preview keeps the current form's star template
      // while estimating the next form's base attributes.
      GC.G().PetStarConf.getDesList().some(function(x){
        if(Number(x.templateId)===Number(parentCfg.starTemplateId)&&
           Number(x.star)===Math.max(1,Number(pet.starLevel)||1)){
          starDes=x;starBonus=Number(x.starAddVal)||0;return true;
        }
        return false;
      });
      pet.insight=Number(pet.insight)||1010;
      insightCfg=GC.G().petInsightConfig.getDes(pet.insight);
    }catch(e){log("local evolution stat config",e);}
    // Match util.USprite.estimateSpiritAttr: use the evolved species' base
    // values, but preserve the current pet's crystal, star, wash, insight,
    // assistant, panel, and equipped-item bonuses.
    var crystalLevel=Number(pet.crystalLevel)||0;
    var levelFactor=.9+.1*(crystalLevel||oldLevel),assist=pet.assitAttr||{},
      gearBonus=localEquipmentBonusForNode(packs[index]);
    var hp=(Number(childCfg.hp)||0)+(Number(pet.washHp)||0);
    hp=hp*levelFactor*(1+starBonus/10000)*
      (1+(Number(insightCfg&&insightCfg.addHp)||0)/10000+
        (Number(assist[12])||0)/10000+(Number(gearBonus.hpPercent)||0)/10000);
    hp=Math.round((hp+(Number(gearBonus.hp)||0))*
      (10000+(Number(pet.panelHp)||0))/10000);
    var attack=(Number(childCfg.attack)||Number(childCfg.basicAttack)||0)+(Number(pet.washAttack)||0);
    attack=Math.round(attack*levelFactor*(1+starBonus/10000)*
      (1+(Number(insightCfg&&insightCfg.addAttack)||0)/10000+
        (Number(assist[13])||0)/10000+(Number(gearBonus.attackPercent)||0)/10000))+
      (Number(gearBonus.attack)||0);
    var defense=(Number(childCfg.defense)||Number(childCfg.basicDefense)||0)+(Number(pet.washDefense)||0);
    defense=Math.round(defense*levelFactor*(1+starBonus/10000)*
      (1+(Number(insightCfg&&insightCfg.addDefense)||0)/10000+
        (Number(assist[14])||0)/10000+(Number(gearBonus.defensePercent)||0)/10000))+
      (Number(gearBonus.defense)||0);
    if(hp<=0||attack<=0||defense<0){r.ret=1;log("local PetGrowupEvolve rejected: invalid new stats",hp,attack,defense);return r;}
    var oldHp=Number(pet.hp)||0,oldAttack=Number(pet.attack)||0,oldDefense=Number(pet.defense)||0;
    var newScore=Math.floor((Number(pet.fightScore)||0)+
      1.1*(hp-oldHp)+10*(attack-oldAttack)+10*(defense-oldDefense));
    inventory.count=Math.max(0,Number(inventory.count||0)-itemCount);
    if(inventory.count===0)delete u.itemPackInfo.idMap[itemId];
    money.gold=long(Number(money.gold||0)-coinCount);
    var oldId=Number(pet.id);
    pet.id=Number(childCfg.id);pet.name=childCfg.name||pet.name;
    pet.hp=long(hp);pet.attack=long(attack);pet.defense=long(defense);
    pet.fightScore=long(newScore);
    pet.starLevel=Number(pet.starLevel)||Number(childCfg.starLevel)||1;
    packs[index].pet=pet;packs[index].state=1;u.petPackInfo.packArray=packs;
    if(u.petStorageInfo&&Array.isArray(u.petStorageInfo.petArray)){
      for(var si=0;si<u.petStorageInfo.petArray.length;si++){
        var stored=u.petStorageInfo.petArray[si];
        if(stored&&String(stored.genId)===String(pet.genId))u.petStorageInfo.petArray[si]=pet;
      }
    }
    localNotifyInventoryChanged(u,true);save();r.ret=0;r.pet=pet;
    log("local PetGrowupEvolve",index,oldId,"->",pet.id,
      "cost",itemId,itemCount,coinCount,
      "stats",String(pet.hp),String(pet.attack),String(pet.defense),String(pet.fightScore));
    return r;
  }
          function makeOfflinePetGrowupRsp(req,r){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(!u||!u.baseInfo){r.ret=1;return r;}
    current=u;var index=Number(req&&req.index),packs=normalizePetPack(u);
    if(!isFinite(index)||Math.floor(index)!==index||index<0||index>=18||!packs[index]||!packs[index].pet){r.ret=1;return r;}
    var pet=packs[index].pet,oldLevel=Number(pet.level)||1,bulk=Number(req&&req.type)===1,changed=0;
    var spiritCfg=null,starDes=null,starBonus=0,insightCfg=null;
    try{
      spiritCfg=GC.G().spiritConfig.getDes(pet.id);
      GC.G().PetStarConf.getDesList().some(function(x){
        if(Number(x.templateId)===Number(spiritCfg.starTemplateId)&&Number(x.star)===Number(pet.starLevel||spiritCfg.quality)){
          starDes=x;starBonus=Number(x.starAddVal)||0;return true;
        }
        return false;
      });
      pet.insight=Number(pet.insight)||1010;
      insightCfg=GC.G().petInsightConfig.getDes(pet.insight);
    }catch(e){log("local pet config lookup",e&&e.stack||e);}
    if(!spiritCfg){r.ret=1;log("local pet config missing",pet.id);return r;}
    pet.assitAttr=pet.assitAttr||{};
    var levelLimit=Number(starDes&&starDes.levelLimit)||100;
    if(!u.petCrystalInfo)u.petCrystalInfo=new rp.PetCrystalInfo();
    function calcOfflinePetStats(level){
      // Mirrors util.USprite.estimateSpiritAttr for the offline profile's
      // no-equipment/no-assistance baseline, while retaining wash/insight
      // and assistant bonuses stored on the PetEntry.
      var levelValue=Number(pet.crystalLevel)||Number(level)||1;
      var levelFactor=.9+.1*levelValue;
      var insightHp=Number(insightCfg&&insightCfg.addHp)||0;
      var insightAttack=Number(insightCfg&&insightCfg.addAttack)||0;
      var insightDefense=Number(insightCfg&&insightCfg.addDefense)||0;
      var assist=pet.assitAttr||{};
      var hp=(Number(spiritCfg.hp)||0)+(Number(pet.washHp)||0);
      hp=hp*levelFactor*(1+starBonus/10000)*(1+insightHp/10000+(Number(assist[12])||0)/10000);
      hp=Math.round(hp*(10000+(Number(pet.panelHp)||0))/10000);
      var attack=(Number(spiritCfg.attack)||0)+(Number(pet.washAttack)||0);
      attack=Math.round(attack*(1+starBonus/10000)*levelFactor*(1+insightAttack/10000+(Number(assist[13])||0)/10000));
      var defense=(Number(spiritCfg.defense)||0)+(Number(pet.washDefense)||0);
      defense=Math.round(defense*levelFactor*(1+starBonus/10000)*(1+insightDefense/10000+(Number(assist[14])||0)/10000));
      return {hp:hp,attack:attack,defense:defense};
    }
    while(changed<120){
      var nextLevel=Number(pet.level||1)+1,nextCfg=GC.G().petLevelConfig.getDes(nextLevel);
      if(!nextCfg||Number(pet.level)>=levelLimit)break;
      if(Number(pet.level)>=120&&Number(pet.level)>=Number(u.petCrystalInfo.crystalLevel||0)+40)break;
      if(!localPetLevelCostAvailable(u,nextCfg))break;
      consumeLocalPetLevelCost(u,nextCfg);
      var oldHp=Number(pet.hp)||Number(spiritCfg.hp)||0;
      var oldAttack=Number(pet.attack)||Number(spiritCfg.attack)||0;
      var oldDefense=Number(pet.defense)||Number(spiritCfg.defense)||0;
      pet.level=nextLevel;
      var stats=calcOfflinePetStats(nextLevel);
      pet.hp=long(stats.hp);pet.attack=long(stats.attack);pet.defense=long(stats.defense);
      var score=Number(pet.fightScore)||0;
      score=Math.floor(score+1.1*(stats.hp-oldHp)+10*(stats.attack-oldAttack)+10*(stats.defense-oldDefense));
      pet.fightScore=long(score);
      changed++;
      if(!bulk)break;
    }
    if(!changed){r.ret=1;log("local pet growup blocked",index,oldLevel,levelLimit);return r;}
    r.ret=0;r.level=pet.level;r.exp=Number(pet.exp)||0;r.pet=pet;r.crystalLevel=Number(u.petCrystalInfo.crystalLevel)||0;
    packs[index].pet=pet;u.petPackInfo.packArray=packs;
    if(u.petStorageInfo&&Array.isArray(u.petStorageInfo.petArray)){
      for(var j=0;j<u.petStorageInfo.petArray.length;j++)if(u.petStorageInfo.petArray[j]&&u.petStorageInfo.petArray[j].genId===pet.genId)u.petStorageInfo.petArray[j]=pet;
    }
    if(changed>0){
      offlineTaskMeta.dailyCounters[40]=(Number(offlineTaskMeta.dailyCounters[40])||0)+1;
      log("local daily pet upgrade progress",offlineTaskMeta.dailyCounters[40]);
    }
    log("local pet growup",index,oldLevel+"->"+pet.level,"hp",String(pet.hp),"attack",String(pet.attack),"defense",String(pet.defense),
      "score",String(pet.fightScore),"gold",String(u.baseInfo.moneyInfo&&u.baseInfo.moneyInfo.gold||0),"point56",Number(u.baseInfo.newPointItemMap&&u.baseInfo.newPointItemMap[56]||0));
    syncOfflineTaskProgress(u);save();return r;
  }
  function combatSpirit(id,level,hp){
    var s=new rp.CombatSpirit();
    s.id=Number(id)||0;s.level=Number(level)||1;
    s.status=s.id?rp.CombatSpiritStatus.ALIVE:rp.CombatSpiritStatus.CSS_UNKNOW;
    s.hp=long(s.id?Math.max(1,Number(hp)||1):0);
    s.fullHp=long(s.id?Math.max(1,Number(hp)||1):0);
    s.oldHp=s.id?Math.max(1,Number(hp)||1):0;
    s.mp=50;s.buffMap={};return s;
  }
  function combatPlayer(id,name,level,entries){
    var p=new rp.CombatPlayer();p.id=(Number(id)===0?0:long(id));p.name=name;p.level=level||1;p.sex=2;
    p.commuSkillId=0;p.warCmdLevel=0;p.warCmdSkill=0;p.godSkill=false;
    p.partner=[combatSpirit(0,1,0)];p.spirits=[];
    for(var i=0;i<6;i++){
      var pet=entries[i];
      p.spirits.push(pet?combatSpirit(pet.id,pet.level,pet.hp):combatSpirit(0,1,0));
    }
    return p;
  }
  function offlineCombatPet(id,level,hp,attack,defense,skillId){
    return {id:Number(id)||0,level:Number(level)||1,hp:Math.max(1,Number(hp)||1),
      fullHp:Math.max(1,Number(hp)||1),attack:Math.max(1,Number(attack)||1),
      defense:Math.max(0,Number(defense)||0),skillId:Number(skillId)||13108,
      mp:50,status:rp.CombatSpiritStatus.ALIVE};
  }
  function offlinePetFromEntry(pet,node){
    if(!pet||!Number(pet.id))return null;
    var cfg=GC.G().spiritConfig.getDes(Number(pet.id));
    if(!cfg)return null;
    var bonus=localEquipmentBonusForNode(node);
    var hp=Number(pet.hp)||Number(cfg.hp)||1;
    var attack=Number(pet.attack)||Number(cfg.attack)||1;
    var defense=Number(pet.defense)||Number(cfg.defense)||0;
    hp=Math.round(hp*(1+(Number(bonus.hpPercent)||0)/10000)+(Number(bonus.hp)||0));
    attack=Math.round(attack*(1+(Number(bonus.attackPercent)||0)/10000)+(Number(bonus.attack)||0));
    defense=Math.round(defense*(1+(Number(bonus.defensePercent)||0)/10000)+(Number(bonus.defense)||0));
    log("local pet equipment bonus",Number(node&&node.index||0),
      "hp",Number(bonus.hp)||0,"attack",Number(bonus.attack)||0,
      "defense",Number(bonus.defense)||0,
      "combat",hp,attack,defense);
    return offlineCombatPet(pet.id,pet.level||1,hp,attack,defense,cfg.basicSkill);
  }
  function offlinePveEnemies(stage){
    var stageCfg=GC.G().NEW_SCENE_GRADE_CONF.getDes(Number(stage));
    var teamId=stageCfg&&stageCfg.fightId&&Number(stageCfg.fightId[0])||0;
    var team=teamId&&GC.G().PVE_TEAM_CONF.getDes(teamId);
    var result=new Array(6);
    result.__offlineConfigValid=true;
    if(!team||!Array.isArray(team.petId)){
      result.__offlineConfigValid=false;
      log("local PVE enemy team missing",Number(stage),teamId);
      return result;
    }
    var expectedEnemies=team.petId.filter(function(id){return Number(id)>0;}).length;
    var loadedEnemies=0;
    for(var i=0;i<6;i++){
      var id=Number(team.petId[i])||0;
      if(!id)continue;
      var pvePet=GC.G().PVE_PET_CONF.getDes(id);
      if(!pvePet){result.__offlineConfigValid=false;continue;}
      var cfg=GC.G().spiritConfig.getDes(Number(pvePet.petId));
      if(!cfg){result.__offlineConfigValid=false;continue;}
      // The archived PVE table provides the opponent's exact species and level;
      // this deterministic local simulator uses that species' base combat stats.
      var level=Number(pvePet.petLevel)||1;
      var factor=1+Math.max(0,level-1)*0.04;
      result[i]=offlineCombatPet(cfg.id,level,Math.round(Number(cfg.hp||1)*factor),
        Math.round(Number(cfg.attack||cfg.basicAttack||1)*factor),
        Math.round(Number(cfg.defense||cfg.basicDefense||0)*factor),cfg.basicSkill);
      loadedEnemies++;
    }
    if(loadedEnemies!==expectedEnemies){
      result.__offlineConfigValid=false;
      log("local PVE enemy config incomplete",Number(stage),loadedEnemies,expectedEnemies);
    }
    return result;
  }
  function offlinePlayerFormation(u){
    var entries=new Array(6),packs=u&&u.petPackInfo&&u.petPackInfo.packArray||[];
    for(var i=0;i<packs.length;i++){
      var node=packs[i],pet=node&&node.pet;
      if(!pet||!Number(pet.id))continue;
      var position=Number(node.combatPos)||((i%6)+1);
      if(position<1||position>6||entries[position-1])continue;
      entries[position-1]=offlinePetFromEntry(pet,node);
    }
    if(!entries.some(function(x){return !!x;})){
      var fallback=petFrom(null);
      entries[0]=offlinePetFromEntry(fallback);
    }
    return entries;
  }
  function offlineAlive(pet){return !!pet&&pet.hp>0&&pet.status!==rp.CombatSpiritStatus.DEAD;}
  function offlineLivingCount(side){return side.filter(offlineAlive).length;}
  function offlineCombatChange(sideIndex,slot,pet,effect,amount,oldHp){
    var change=new rp.CombatSpiritDataChange();
    change.pos=(sideIndex<<4)+slot;change.effect=effect;
    change.oldValue=Math.max(0,Number(oldHp)||0);change.value=long(Math.max(0,Number(amount)||0));
    var next=new rp.CombatSpirit();
    next.id=pet.id;next.level=pet.level;next.status=offlineAlive(pet)?rp.CombatSpiritStatus.ALIVE:rp.CombatSpiritStatus.DEAD;
    next.hp=long(Math.max(0,pet.hp));next.fullHp=long(pet.fullHp);next.oldHp=Math.max(0,Number(oldHp)||0);
    next.mp=pet.mp||0;next.buffMap={};change.data=next;
    return change;
  }
  function offlineSkillFor(pet){
    var skill=pet&&GC.G().skillConfig.getDes(Number(pet.skillId)||13108);
    return skill||GC.G().skillConfig.getDes(13108);
  }
  function offlineLowestHpTarget(side){
    var best=-1,ratio=2;
    for(var i=0;i<side.length;i++){
      if(!offlineAlive(side[i]))continue;
      var r=side[i].hp/Math.max(1,side[i].fullHp);
      if(r<ratio){ratio=r;best=i;}
    }
    return best;
  }
  function offlineApplySkill(steps,actorSide,slot,round,actor,ownSide,enemySide){
    if(!offlineAlive(actor))return;
    var skill=offlineSkillFor(actor),logic=Number(skill&&skill.logics&&skill.logics[0]&&skill.logics[0].logic)||1;
    var percent=Number(skill&&skill.logics&&skill.logics[0]&&skill.logics[0].param2)||100;
    var healing=logic===3,targetSide=healing?ownSide:enemySide,targetSideIndex=healing?actorSide:1-actorSide;
    var targets=[];
    if(healing){
      var healTarget=offlineLowestHpTarget(targetSide);
      if(healTarget>=0&&targetSide[healTarget].hp<targetSide[healTarget].fullHp)targets.push(healTarget);
    }else if(Number(skill&&skill.opparea)===17){
      for(var i=0;i<targetSide.length;i++)if(offlineAlive(targetSide[i]))targets.push(i);
    }else{
      for(var j=0;j<targetSide.length;j++)if(offlineAlive(targetSide[j])){targets.push(j);break;}
    }
    if(!targets.length)return;
    var step=new rp.CombatOneStep();step.doWhat=rp.CombatStepType.SKILL;
    step.skillId=Number(skill&&skill.id)||actor.skillId;step.source=(actorSide<<4)+slot;step.round=round;step.changes=[];
    for(var k=0;k<targets.length;k++){
      var index=targets[k],target=targetSide[index],oldHp=target.hp,amount;
      if(healing){
        amount=Math.max(1,Math.floor(actor.attack*percent/100));
        target.hp=Math.min(target.fullHp,target.hp+amount);target.status=rp.CombatSpiritStatus.ALIVE;
      }else{
        amount=Math.max(1,Math.floor((actor.attack*percent/100)-target.defense*0.2));
        target.hp=Math.max(0,target.hp-amount);
        if(target.hp<=0)target.status=rp.CombatSpiritStatus.DEAD;
      }
      step.changes.push(offlineCombatChange(targetSideIndex,index,target,
        healing?rp.CombatSkillEffect.HEAL:rp.CombatSkillEffect.NORMAL_ATTACK,
        Math.abs(target.hp-oldHp),oldHp));
    }
    steps.push(step);
  }
  function makeOfflineCombat(stage){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    var playerSide=offlinePlayerFormation(u),enemySide=offlinePveEnemies(stage);
    var playerLevel=1;
    playerSide.forEach(function(p){if(p)playerLevel=Math.max(playerLevel,p.level);});
    var data=new rp.OneCombatData();data.type=rp.CombatType.PVE;
    data.players=[
      combatPlayer(u&&u.baseInfo&&u.baseInfo.userId||UID,u&&u.baseInfo&&u.baseInfo.name||NAME,playerLevel,playerSide),
      combatPlayer(0,"离线训练对手",1,enemySide)
    ];
    var begin=new rp.CombatOneStep();begin.doWhat=rp.CombatStepType.START;begin.round=1;begin.source=0;
    data.steps=[begin];
    var maxRounds=12,round=0;
    for(var r=1;r<=maxRounds;r++){
      round=r;
      if(r>1){var roundStep=new rp.CombatOneStep();roundStep.doWhat=rp.CombatStepType.ROUND;roundStep.round=r;roundStep.source=0;data.steps.push(roundStep);}
      for(var side=0;side<2;side++){
        var actors=side===0?playerSide:enemySide;
        for(var slot=0;slot<6;slot++){
          if(!offlineLivingCount(side===0?enemySide:playerSide))break;
          var actor=actors[slot];
          if(!offlineAlive(actor))continue;
          offlineApplySkill(data.steps,side,slot,r,actor,actors,side===0?enemySide:playerSide);
        }
      }
      var roundEnd=new rp.CombatOneStep();roundEnd.doWhat=rp.CombatStepType.ROUND_END;
      roundEnd.round=r;roundEnd.source=0;roundEnd.changes=[];data.steps.push(roundEnd);
      if(!offlineLivingCount(enemySide)||!offlineLivingCount(playerSide))break;
    }
    var playerAlive=offlineLivingCount(playerSide),enemyAlive=offlineLivingCount(enemySide);
    var playerCount=playerSide.filter(function(p){return !!p;}).length;
    var enemyCount=enemySide.filter(function(p){return !!p;}).length;
    data.result=enemyCount===0||enemySide.__offlineConfigValid===false?rp.CombatResult.LOSE:
      enemyAlive===0?rp.CombatResult.WIN:playerAlive===0?rp.CombatResult.LOSE:
      playerSide.reduce(function(sum,p){return sum+(offlineAlive(p)?p.hp:0);},0)>=
      enemySide.reduce(function(sum,p){return sum+(offlineAlive(p)?p.hp:0);},0)?rp.CombatResult.WIN:rp.CombatResult.LOSE;
    var finish=new rp.CombatOneStep();finish.doWhat=rp.CombatStepType.END;finish.round=round;finish.source=0;
    data.steps.push(finish);data.totalRound=round;data.time=Math.max(3,round*3);data.rewards=[];
    data.ownDeadPetNum=playerCount-playerAlive;data.enermyDeadPetNum=enemyCount-enemyAlive;
    log("local combat simulation","stage",stage,"rounds",round,"steps",data.steps.length,
      "players",playerAlive+"/"+playerCount,"enemies",enemyAlive+"/"+enemyCount,"result",data.result);
    return data;
  }
  function makeOfflineSceneFight(req){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    if(u)current=u;
    var oldLevel=u&&u.newSceneGradeInfo&&Number(u.newSceneGradeInfo.sceneLevel)||1;
    var nextLevel=oldLevel+1;
    var cfg=GC.G().NEW_SCENE_GRADE_CONF.getDes(nextLevel);
    if(!cfg){nextLevel=1;cfg=GC.G().NEW_SCENE_GRADE_CONF.getDes(nextLevel);}
    var rsp=new rp.NewSceneGradeFightRsp();rsp.ret=0;rsp.sceneLevel=nextLevel;
    rsp.sceneMapId=cfg&&cfg.sceneId||1;rsp.quickFightTimes=0;rsp.freeTimes=1;
    rsp.level=cfg&&cfg.level||1;rsp.nextLevelExp=long(0);
    var result=new rp.NewSceneResultInfo(),combat=makeOfflineCombat(nextLevel);
    result.sceneLevel=nextLevel;result.fightData=[combat];rsp.fightInfo=[result];
    if(combat.result!==rp.CombatResult.WIN){
      rsp.sceneLevel=oldLevel;
      rsp.sceneMapId=u&&u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneMapId||cfg&&cfg.sceneId||1;
      result.sceneLevel=oldLevel;rsp.actionArr=[];
      log("local scene battle lost; progression retained",oldLevel,"attempted",nextLevel);
      return rsp;
    }
    rsp.actionArr=(cfg&&cfg.actionArr||[]).map(function(a){
      var params=Array.isArray(a.params)?a.params.slice():[];
      if(!params.length){if(a.para1!=null)params.push(a.para1);if(a.para2!=null)params.push(a.para2);}
      return offlineAction(a.type,params);
    });
    if(!rsp.actionArr.length)rsp.actionArr=[offlineAction(rp.Action.ActionTye.ADD_GOLD,[10000])];
    if(result.fightData[0])result.fightData[0].rewards=rsp.actionArr;
    var gold=0;
    rsp.actionArr.forEach(function(a){
      var type=Number(a.type);
      if(type===Number(rp.Action.ActionTye.ADD_GOLD))gold+=Number(a.params&&a.params[0]||0);
      else applyLocalRewardAction(a);
    });
    if(gold<=0){
      gold=10000;
      rsp.actionArr.push(offlineAction(rp.Action.ActionTye.ADD_GOLD,[gold]));
    }
    log("local scene reward actions",rsp.actionArr.map(function(a){return String(a.type)+":"+(a.params||[]).join(",");}).join("|"));
    addLocalGold(gold);
    if(u&&u.newSceneGradeInfo){u.newSceneGradeInfo.sceneLevel=nextLevel;u.newSceneGradeInfo.sceneMapId=rsp.sceneMapId;}
    save();log("local NewSceneGradeFightRsp",oldLevel,"->",nextLevel,"fightCount",result.fightData.length);
    return rsp;
  }
  function userInfo(){
    if(saved.restored&&saved.restored.baseInfo){
      current=saved.restored;
      log("local save restored",String(current.baseInfo.moneyInfo&&current.baseInfo.moneyInfo.gold||0),Number(current.newSceneGradeInfo&&current.newSceneGradeInfo.sceneLevel||1));
      var restoredPet=current.petPackInfo&&current.petPackInfo.packArray&&current.petPackInfo.packArray[0]&&current.petPackInfo.packArray[0].pet;
      log("local save restored pet",Number(restoredPet&&restoredPet.level||0),String(restoredPet&&restoredPet.hp||0),String(restoredPet&&restoredPet.attack||0),String(restoredPet&&restoredPet.defense||0));
      var restoredPoints=current.baseInfo.newPointItemMap||{};
      log("local save restored points",Number(restoredPoints[56]||0),Number(restoredPoints[59]||0));
      var restoredCrystal=localRefreshPetCrystal(current);
      var restoredCrystalSlot=restoredCrystal&&restoredCrystal.slotInfo&&restoredCrystal.slotInfo[7];
      var restoredStarTestPet=(current.petStorageInfo.petArray||[]).find(function(x){return Number(x&&x.id)===1108;});
      log("local save restored star-up pet",Number(restoredStarTestPet&&restoredStarTestPet.starLevel)||0);
      var restoredStarBatch=(current.petStorageInfo.petArray||[]).filter(function(x){
        return Number(x&&x.id)===1108&&Number(x.starLevel)===3;
      });
      log("local save restored star-up batch",Math.min(restoredStarBatch.length,2));
      var restoredCardStarPet=(current.petPackInfo.packArray||[]).find(function(node){
        return node&&node.pet&&Number(node.pet.genId)===100001;
      });
      log("local save restored card-star-up pet",
        Number(restoredCardStarPet&&restoredCardStarPet.pet&&restoredCardStarPet.pet.starLevel)||0);
      var restoredItems=current.itemPackInfo&&current.itemPackInfo.idMap||{};
      log("local save restored pet crystal",Number(restoredCrystal&&restoredCrystal.type)||0,
        Number(restoredCrystal&&restoredCrystal.crystalLevel)||0,
        Number(restoredCrystalSlot&&restoredCrystalSlot.slotType)||0,
        Number(restoredCrystalSlot&&restoredCrystalSlot.genId)||0);
      log("local save restored hangup",Number(offlineTaskMeta.lastHangupTime)||0,
        Number(offlineTaskMeta.dailyCounters&&offlineTaskMeta.dailyCounters[52])||0,
        expectedHangupRestore>0?(hangupRestoredAfterDayReset?"PRESERVED":"NOT_PRESERVED"):"UNTESTED");
      log("local save restored quick hangup",quickCombatUsed);
      if(expectedHangupRestore>0)delete offlineTaskMeta.expectedHangupRestoreTime;
      log("local save restored item operations",
        Number(restoredItems[3000002]&&restoredItems[3000002].count||0),
        Number(restoredItems[1000590]&&restoredItems[1000590].count||0));
      if(!current.extInfo)current.extInfo=new rp.UserExtInfo();
      if(!current.extInfo.newGuildInfo)current.extInfo.newGuildInfo=new rp.NewGuildInfo();
      current.extInfo.newGuildInfo.version=0;current.extInfo.newGuildInfo.steps=current.extInfo.newGuildInfo.steps||{};
      var restoredEvolutionPet=(current.petPackInfo.packArray||[]).find(function(node){
        return node&&node.pet&&Number(node.pet.genId)===880001;
      });
      log("local save restored pet evolution",
        Number(restoredEvolutionPet&&restoredEvolutionPet.pet&&restoredEvolutionPet.pet.id)||0);
      log("local save restored pet evolution gear",
        Number(restoredEvolutionPet&&restoredEvolutionPet.pet&&
          localEquipmentBonusForNode(restoredEvolutionPet).hp)||0);
      if(!current.guideScheduleInfo)current.guideScheduleInfo=new rp.GuideActiveSchedule();
      if(!current.guideScheduleInfo.riseStepByStep)current.guideScheduleInfo.riseStepByStep=new rp.GuideActive();
      current.guideScheduleInfo.riseStepByStep.isFinish=1;
      if(!current.collectCardInfo)current.collectCardInfo=new rp.CardCollectInfo();
      if(!current.collectCardInfo.nowSeason||!GC.G().CARD_COLLECT_SEASON_CONF.getDes(current.collectCardInfo.nowSeason))current.collectCardInfo.nowSeason=currentCardSeason();
      if(!current.petRoomInfo)current.petRoomInfo=new rp.PetRoomInfo();
      normalizeGuideSchedule(current);normalizePetPack(current);
      ensureOfflineTaskInfo(current);
      normalizeLocalEquipmentInventory(current);
      var restoredEquipCount=(current.petPackInfo.packArray||[]).reduce(function(sum,node){
        return sum+(node&&node.equip||[]).filter(function(x){return x&&localEquipmentPosition(x.id)>0;}).length;
      },0);
      log("local save restored inventory",
        current.petPackInfo.packArray.length,
        current.petStorageInfo.petArray.length,
        Object.keys(current.itemPackInfo&&current.itemPackInfo.idMap||{}).length);
      log("local save restored equipment",restoredEquipCount,
        Object.keys(current.itemPackInfo&&current.itemPackInfo.sidMap||{}).length);
      return current;
    }
    var u=new rp.UserDataInfo(), b=new rp.UserBaseInfo(), old=saved.userInfo&&saved.userInfo.baseInfo||{};
    b.userId=long(old.userId||UID);b.name=old.name||NAME;b.sex=old.sex||2;b.level=Math.max(1,Number(old.level)||1);
    b.vipLevel=Number(old.vipLevel)||0;b.zoneId=1;b.sceneLevel=Math.max(1,Number(old.sceneLevel)||1);
    b.sceneLevelTimes=Number(old.sceneLevelTimes)||0;b.firstPet=3101;b.sid="offline-local";b.loginWay=102;b.platform="offline";b.mixWay=4;b.avatarId=Number(old.avatarId)||1;
    b.moneyInfo=new rp.MoneyInfo();var m=old.moneyInfo||{};
    b.moneyInfo.gold=long(m.gold==null?1000000:m.gold);b.moneyInfo.diamond=Number(m.diamond==null?10000:m.diamond);
    b.moneyInfo.cash=Number(m.cash==null?10000:m.cash);b.moneyInfo.petCoin=long(m.petCoin||100000);b.moneyInfo.equipCoin=long(m.equipCoin||100000);
    b.moneyInfo.warScoreCoin=long(m.warScoreCoin||0);b.moneyInfo.honorCoin=long(m.honorCoin||0);b.moneyInfo.rankGameScore=Number(m.rankGameScore)||0;
    b.newPointItemMap=old.newPointItemMap||{};
    if(b.newPointItemMap[56]==null)b.newPointItemMap[56]=5000;
    log("local point item initial",56,Number(b.newPointItemMap[56]||0));
    u.baseInfo=b;
    u.extInfo=new rp.UserExtInfo();
    u.extInfo.newGuildInfo=new rp.NewGuildInfo();u.extInfo.newGuildInfo.version=0;u.extInfo.newGuildInfo.steps={};
    u.itemPackInfo=new rp.ItemPackInfo();u.itemPackInfo.idMap={};
    u.petPackInfo=new rp.PetPackInfo();u.petStorageInfo=new rp.PetStorageInfo();
    var savedPack=saved.petPackInfo&&saved.petPackInfo.packArray||[];
    var prior=savedPack[0]&&savedPack[0].pet;
    var p=petFrom(prior),packs=[];
    for(var i=0;i<18;i++){
      var source=savedPack[i]||null,n=new rp.PackNode();
      if(source)Object.keys(source).forEach(function(k){n[k]=source[k];});
      n.index=i+1;n.equip=Array.isArray(n.equip)?n.equip:[];
      n.pet=source&&source.pet?petFrom(source.pet):null;
      if(i===0&&!n.pet)n.pet=p;
      n.state=n.pet?1:0;
      n.combatPos=n.pet?(Number(source&&source.combatPos)||((i%6)+1)):0;
      packs.push(n);
    }
    u.petPackInfo.packArray=packs;
    var storedPets=saved.petStorageInfo&&saved.petStorageInfo.petArray;
    u.petStorageInfo.petArray=Array.isArray(storedPets)&&storedPets.length?storedPets.map(function(x){return petFrom(x);}):[p];
    u.petStorageInfo.sidGenerator=Number(saved.petStorageInfo&&saved.petStorageInfo.sidGenerator)||100002;
    var storedItems=saved.itemPackInfo&&saved.itemPackInfo.idMap||{};
    Object.keys(storedItems).forEach(function(id){
      var raw=storedItems[id]||{},item=new rp.ItemBase();
      Object.keys(raw).forEach(function(k){item[k]=raw[k];});
      item.id=Number(item.id)||Number(id);item.count=Math.max(0,Number(item.count)||0);
      u.itemPackInfo.idMap[id]=item;
    });
    u.itemPackInfo.sidMap={};
    var storedSidItems=saved.itemPackInfo&&saved.itemPackInfo.sidMap||{};
    Object.keys(storedSidItems).forEach(function(sid){
      var raw=storedSidItems[sid]||{},item=new rp.ItemBase();
      Object.keys(raw).forEach(function(k){item[k]=raw[k];});
      item.sid=localLongValue(raw.sid==null?sid:raw.sid);
      item.id=Number(item.id)||0;item.count=1;
      u.itemPackInfo.sidMap[String(item.sid)]=item;
    });
    u.itemPackInfo.sidGenerator=localLongValue(saved.itemPackInfo&&saved.itemPackInfo.sidGenerator||100002);
    u.sceneBagInfo=new rp.SceneBagInfo();u.sceneBagInfo.sceneBag=new rp.SceneStorageBag();u.sceneBagInfo.limitInfo=new rp.SceneLimitInfo();
    u.redotInfo=new rp.RedotInfo();u.activityInfo=new rp.ActivityInfo();u.petRoomInfo=new rp.PetRoomInfo();u.happyBeachInfo=new rp.HappyBeachInfo();
    u.newSceneGradeInfo=new rp.NewSceneGradeInfo();
    var savedGrade=saved.newSceneGradeInfo||{};
    u.newSceneGradeInfo.sceneLevel=Math.max(1,Number(savedGrade.sceneLevel)||Number(old.sceneLevel)||1);
    u.newSceneGradeInfo.sceneMapId=Number(savedGrade.sceneMapId)||1;
    u.growthFound=new rp.GrowthFound();
    u.collectCardInfo=new rp.CardCollectInfo();u.collectCardInfo.nowSeason=currentCardSeason();
    if(!GC.G().CARD_COLLECT_SEASON_CONF.getDes(u.collectCardInfo.nowSeason))u.collectCardInfo.nowSeason=19;
    var typed={
      teamPkEffectInfo:"PkAttrInfo",relicInfo:"UserRelicInfo",shopInfo:"ShopInfo",hallInfo:"DBHallInfo",
      monopolyInfo:"DBMonopolyInfo",assitPetPackInfo:"AssitPetPackInfo",treasureInfo:"DBTreasureInfo",
      petBookInfo:"PetBookInfo",titleInfo:"TitleInfo",happyBeachInfo:"HappyBeachInfo",
      userGuildInfo:"UserGuildInfo",checkInfo:"CheckInInfo",taskInfo:"DBAllTaskInfo",
      petGrowTaskInfo:"PetGrowTaskInfo",guideScheduleInfo:"GuideActiveSchedule",
      dailyConsumptionActivityInfo:"DailyConsumptionActivityInfo",rideInfo:"DBRideInfo",
      commInfo:"DBCommunicateInfo",rankGameInfo:"DBRankGameInfo",activityShopInfo:"DBActivityShopInfo",
      petRoomInfo:"PetRoomInfo",superHallInfo:"DBSuperHallInfo",guildImageSpiriteInfo:"PkAttrInfo",
      chatBlacklistInfo:"ChatBlacklistInfo",warCmdInfo:"WarCmdUserInfo",artifactBooksInfo:"ArtifactBookMapInfo",
      cashFundInfo:"CashFundInfo",summerPetInfo:"DBSummerPetInfo",rechargeTurntableInfo:"DbRechargeTurntableInfo",
      spriteSkinMapInfo:"SpriteSkinInfo",spriteSkinRedotInfo:"SpriteSkinRedotInfo",srspiriteInfo:"DBSrSpiriteInfo",
      yearClbtInfo:"DBYearClbtInfo",headIconsInfo:"HeadIconsInfo",specialActivityMap:"DBSpecialActivity",
      userMazeInfo:"MazeUserInfo",advAwardInfo:"LookAdvAwardInfo",partnerInfo:"DBPartnerInfo",
      topAreaInfo:"DBTopAreaInfo",sharedCrystalInfo:"UserSharedCrystalInfo",warAreaInfo:"DBWarAreaInfo",
      endlessAbyssInfo:"DBEndlessAbyssInfo",newSportsInfo:"NewSportsInfo",petCrystalInfo:"PetCrystal",
      newEquipCombine:"NewEquipCombine",newChampInfo:"NewChampInfo",timeSpaceCrackInfo:"TimeAndSpaceCrackInfo",
      newStoreInfo:"NewStoreInfo",legendaryChallengeInfo:"LegendaryChallengeInfo",offerRewardInfo:"OfferRewardInfo",
      eliteCallInfo:"EliteCallInfo",limitTimeAdvent:"LimitTimeAdventInfo",weekCircles:"UserWeekCircleInfo",
      newVersionFixInfo:"NewVersionFixInfo",newTaskInfo:"DBNewTaskInfo",userDateAttrInfo:"UserDataAttrInfo",
      naturePowerInfo:"NaturePowerInfo",collectCardInfo:"CardCollectInfo",checkInfo2:"CheckInInfo2",
      checkInfoCycle:"CheckInInfo2",mibaoPackInfo:"MibaoPackInfo",mibaoLotteryInfo:"MibaoLotteryInfo"
    };
    Object.keys(typed).forEach(function(k){try{u[k]=new rp[typed[k]]();}catch(e){log("proto field init",k,e);}});
    u.petCrystalInfo.crystalLevel=1;
    u.newSceneGradeInfo.sceneLevel=1;u.newSceneGradeInfo.sceneMapId=1;
    if(!u.guideScheduleInfo)u.guideScheduleInfo=new rp.GuideActiveSchedule();
    if(!u.guideScheduleInfo.riseStepByStep)u.guideScheduleInfo.riseStepByStep=new rp.GuideActive();
    u.guideScheduleInfo.riseStepByStep.isFinish=1;
    normalizeGuideSchedule(u);normalizePetPack(u);
    ensureOfflineTaskInfo(u);
    normalizeLocalEquipmentInventory(u);
    var restoredEquipCount=(u.petPackInfo.packArray||[]).reduce(function(sum,node){
      return sum+(node&&node.equip||[]).filter(function(x){return x&&localEquipmentPosition(x.id)>0;}).length;
    },0);
    log("local JSON fallback restored equipment",restoredEquipCount,
      Object.keys(u.itemPackInfo&&u.itemPackInfo.sidMap||{}).length);
    log("local JSON fallback restored inventory",
      u.petPackInfo.packArray.length,u.petStorageInfo.petArray.length,
      Object.keys(u.itemPackInfo&&u.itemPackInfo.idMap||{}).length,
      Number(u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneLevel||1));
    return u;
  }
  function jsonSaveCopy(value){
    if(value==null)return value;
    try{return JSON.parse(JSON.stringify(value));}
    catch(e){log("JSON fallback clone error",e);return null;}
  }
  function save(){
    try{
      var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
      if(!u||!u.baseInfo)return;
      normalizeLocalEquipmentInventory(u);
      var p=u.petPackInfo&&u.petPackInfo.packArray&&u.petPackInfo.packArray[0]&&u.petPackInfo.packArray[0].pet;
      var m=u.baseInfo.moneyInfo||new rp.MoneyInfo();
      var packSnapshot=jsonSaveCopy(u.petPackInfo);
      if(!packSnapshot)packSnapshot={packArray:[{index:1,state:1,combatPos:1,equip:[],pet:jsonSaveCopy(p)}]};
      var storageSnapshot=jsonSaveCopy(u.petStorageInfo);
      if(!storageSnapshot)storageSnapshot={sidGenerator:100002,petArray:p?[jsonSaveCopy(p)]:[]};
      var itemSnapshot=jsonSaveCopy(u.itemPackInfo)||{idMap:{}};
      var gradeSnapshot=jsonSaveCopy(u.newSceneGradeInfo)||{
        sceneLevel:Number(u.baseInfo.sceneLevel)||1,sceneMapId:1
      };
      var x={
        version:6,quickCombatUsed:quickCombatUsed,
        userInfo:{baseInfo:{
          userId:String(u.baseInfo.userId),name:u.baseInfo.name,sex:u.baseInfo.sex,
          level:u.baseInfo.level,vipLevel:u.baseInfo.vipLevel,sceneLevel:u.baseInfo.sceneLevel,
          avatarId:u.baseInfo.avatarId,newPointItemMap:u.baseInfo.newPointItemMap||{},
          moneyInfo:{
            gold:String(m.gold||0),diamond:m.diamond||0,cash:m.cash||0,
            petCoin:String(m.petCoin||0),equipCoin:String(m.equipCoin||0),
            warScoreCoin:String(m.warScoreCoin||0),honorCoin:String(m.honorCoin||0),
            rankGameScore:m.rankGameScore||0
          }
        }},
        petPackInfo:packSnapshot,petStorageInfo:storageSnapshot,
        itemPackInfo:itemSnapshot,newSceneGradeInfo:gradeSnapshot,
        offlineTaskMeta:jsonSaveCopy(offlineTaskMeta)||{}
      };
      try{
        var bytes=rp.UserDataInfo.encode(u).finish(),binary="";
        for(var i=0;i<bytes.length;i++)binary+=String.fromCharCode(bytes[i]);
        x.proto=btoa(binary);
      }catch(protoError){log("protobuf save fallback",protoError);}
      var persisted={
        version:x.version,quickCombatUsed:quickCombatUsed,userInfo:x.userInfo,
        petPackInfo:x.petPackInfo,petStorageInfo:x.petStorageInfo,
        itemPackInfo:x.itemPackInfo,newSceneGradeInfo:x.newSceneGradeInfo,
        offlineTaskMeta:x.offlineTaskMeta
      };
      if(x.proto)persisted.proto=x.proto;
      localStorage.setItem(KEY,JSON.stringify(persisted));
      x.restored=u;saved=x;
    }catch(e){log("save error",e&&e.stack||e);}
  }
  function bots(){
    return ["【模拟】小星","【模拟】阿风","【模拟】皮皮","【模拟】训练员07","【模拟】小羽","【模拟】阿光"].map(function(n,i){
      var b=new rp.UserSnapInfo();b.userId=long(910001+i);b.name=n;b.sex=i%2?1:2;b.level=1+i*3;b.vipLevel=0;b.zoneId=1;b.avatarId=1+i%5;
      b.leader=new rp.GlobalPetSnap();b.leader.id=3101+i%4;b.leader.level=b.level;b.petPackInfo=new rp.PetPackInfo();return b;
    });
  }
  function hookOfflineGiftChoice(cls){
    try{
      var proto=cls&&cls.prototype;
      if(!proto||typeof proto.doOpen!=="function"||proto.__offlineGiftChoiceHook)return;
      var original=proto.doOpen;
      proto.doOpen=function(){
        window.__offlineSelectedGiftIndex=Math.max(0,Number(this.selectIndex)||0);
        log("local gift choice selected",window.__offlineSelectedGiftIndex);
        return original.apply(this,arguments);
      };
      proto.__offlineGiftChoiceHook=true;
    }catch(e){log("local gift choice hook",e&&e.stack||e);}
  }
  try{
    if(typeof mdl!=="undefined"&&mdl.NewBag){
      hookOfflineGiftChoice(mdl.NewBag.CompositeGift);
      hookOfflineGiftChoice(mdl.NewBag.CompositeNewGift);
    }
  }catch(e){log("local gift choice hook init",e&&e.stack||e);}
  if(typeof QuickSdkMgr!=="undefined"){
    QuickSdkMgr.prototype.init=function(){log("SDK bypass");return Promise.resolve();};
    QuickSdkMgr.prototype.showPrivace=function(cb){var x={status:true,message:"offline"};cb&&cb(x);return Promise.resolve(x);};
    QuickSdkMgr.prototype.login=function(cb){var d={uid:"offline-730001",username:NAME,token:"offline-local-token",isLogin:true,channelId:"offline",oaid:""};this._isLogin=true;this._userInfo=d;var x={status:true,channelId:"offline",data:d};cb&&cb(x);log("local identity ready");};
    QuickSdkMgr.prototype.getOaid=function(){return "";};QuickSdkMgr.prototype.role=function(){save();};
    QuickSdkMgr.prototype.pay=function(o,cb){var x={status:false,message:"离线版本不连接真实支付，请使用本地离线菜单"};cb&&cb(x);return x;};
    QuickSdkMgr.prototype.adVideo=function(t,cb){var x={status:false,message:"离线版本不提供广告"};cb&&cb(x);return x;};
    QuickSdkMgr.prototype.share=function(t,cb){var x={status:false,message:"离线版本不连接分享服务"};cb&&cb(x);return x;};
    QuickSdkMgr.prototype.adManExtraPay2Interval=function(){};QuickSdkMgr.prototype.tickHeartBeat=function(){};QuickSdkMgr.prototype.exitGame=function(){};
  }
  if(typeof GameMainBase!=="undefined"){
    var init=GameMainBase.prototype.init;
    GameMainBase.prototype.init=function(){init.call(this);Laya.URL.basePath="file:///android_asset/game/";log("local resource base",Laya.URL.basePath);};
    GameMainBase.prototype.initSdk=function(){return Promise.resolve();};
    GameMainBase.prototype.showNotice=function(){return Promise.resolve();};
  }
  if(typeof NM!=="undefined"){
    NM.prototype.httpCmd=function(c){
      log("local HTTP",c);
      if(c==="svr_list")return Promise.resolve({ret:0,svr_list:[{zone_id:1,user_id:UID,name:"本地离线服",status:1,repair:0}],in_white_list:1,login_svr_id_list:[1],sid:"offline-local",token:"offline-local-token",submit_flag:0,cvv:""});
      if(c==="dir")return Promise.resolve({ret:0,ip:"127.0.0.1",port:19999,city:99,share_flag:0});
      if(c==="ip_level")return Promise.resolve({ret:0,level:0});
      if(c==="notice")return Promise.resolve({ret:0,dir_notice_list:[]});
      return Promise.resolve({ret:1,msg:"离线模式：服务端请求已禁用",offline:true});
    };
    try{Object.defineProperty(NM.prototype,"isConnected",{configurable:true,get:function(){return true;}});}catch(_){}
    NM.prototype.init=function(host,port,onConnect){
      this._offlineConnection=true;
      if(this.socketClient){this.socketClient.destroy=function(){};this.socketClient.connect=function(){};this.socketClient.sendData=function(){return {trans_id:0};};}
      log("local socket stub",host,port);
      setTimeout(function(){try{if(onConnect&&onConnect.run)onConnect.run();else if(typeof onConnect==="function")onConnect();}catch(e){log("connect cb",e);}},0);
    };
    NM.prototype.request=function(req,Resp,cb,ctx){
      var r=new Resp();r.ret=0;
      log("local protobuf",req&&req.constructor&&req.constructor.name,Resp&&Resp.name);
      try{for(var key in r)if(r[key]===null)r[key]={};}catch(_){}
      if(Resp===rp.LoginRsp){r.ret=0;r.userInfo=userInfo();normalizeGuideSchedule(r.userInfo);normalizePetPack(r.userInfo);current=r.userInfo;log("login guide defaults",!!r.userInfo.guideScheduleInfo,!!r.userInfo.guideScheduleInfo.riseStepByStep);r.serverMtime=long(Date.now());r.userLeadValue=[];r.offineInfo=new rp.OffineLineInfo();
        r.openSvrDays=20;r.openSvrTime=Math.floor(Date.now()/1000)-20*86400;r.mergeSvrDays=0;r.mergeSvrTime=0;r.loginNotice={title:"",nickName:"",content:"",name:"",date:""};log("local LoginRsp");}
      else if(Resp===rp.HeartBeatRsp){r.ret=0;r.serverMtime=long(Date.now());log("local heartbeat");}
      else if(Resp===rp.EnterSceneRsp){r.ret=0;r.sceneId=req&&req.sceneId||1;r.sceneName="离线精灵城";r.userInfos=bots();r.sceneBag=new rp.SceneBag();r.sceneBag.maxItemNum=200;r.sceneBag.curItemNum=0;r.sceneBag.maxSpiritNum=100;r.sceneBag.curSpiritNum=100;r.sceneBag.expCoinPercent=100;r.sceneBag.sceneLevelTimes=0;r.sceneBag.sceneLevel=1;log("local EnterSceneRsp + labelled bots");}
      else if(Resp===rp.NewSceneGradeFightRsp){
        r=makeOfflineSceneFight(req);
      }
      else if(Resp===rp.GetPkAttrInfoRsp){
        var attrUser=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
        var petIndex=Number(req&&req.petIndex);
        var petNode=attrUser&&attrUser.petPackInfo&&attrUser.petPackInfo.packArray&&attrUser.petPackInfo.packArray[petIndex];
        if(!petNode&&attrUser&&attrUser.petPackInfo&&attrUser.petPackInfo.packArray&&attrUser.petPackInfo.packArray[petIndex-1])petNode=attrUser.petPackInfo.packArray[petIndex-1];
        var gearBonus=localEquipmentBonusForNode(petNode);
        r.ret=0;r.attr=localApplyEquipmentBonusToAttr(new rp.PkAttrInfo(),gearBonus);
        r.teamPkAttr=new rp.PkAttrInfo();
        r.evaluteHpAbs=0;r.evaluteHpPersent=0;
        r.evaluteAttackAbs=0;r.evaluteAttackPersent=0;
        r.evaluteDefenseAbs=0;r.evaluteDefensePersent=0;
        log("local pet attributes calculated",petIndex,
          "equipment",Number(gearBonus.hp)||0,Number(gearBonus.attack)||0,Number(gearBonus.defense)||0);
      }
      else if(Resp===rp.PetCrystalInfoRsp){
        r=makeOfflinePetCrystalInfoRsp(r);
      }
      else if(Resp===rp.PetCrystalSetRsp){
        r=makeOfflinePetCrystalSetRsp(req,r);
      }
      else if(Resp===rp.PetCrystalGetRsp){
        r=makeOfflinePetCrystalGetRsp(req,r);
      }
      else if(Resp===rp.PetCrystalUnlockRsp){
        r=makeOfflinePetCrystalUnlockRsp(req,r);
      }
      else if(Resp===rp.PetCrystalBuyCoolTimeRsp){
        r=makeOfflinePetCrystalBuyCoolTimeRsp(req,r);
      }
      else if(Resp===rp.PetCrystalBreakRsp){
        r=makeOfflinePetCrystalBreakRsp(r);
      }
      else if(Resp===rp.PetStarLevelUpRsp){
        r=makeOfflinePetStarLevelUpRsp(req,r);
      }
      else if(Resp===rp.OnePetStarLevelUpRsp){
        r=makeOfflineOnePetStarLevelUpRsp(req,r);
      }
      else if(Resp===rp.PetGrowupEvolveRsp){
        r=makeOfflinePetGrowupEvolveRsp(req,r);
      }
      else if(Resp===rp.PetGrowupExpRsp){
        r=makeOfflinePetGrowupRsp(req,r);
      }
      else if(Resp===rp.GetPetStorageRsp){
        r=makeOfflinePetStorageRsp(r);
      }
      else if(Resp===rp.UseItemRsp){
        r=makeOfflineUseItemRsp(req,r);
      }
      else if(Resp===rp.MixturePetRsp){
        r=makeOfflineMixturePetRsp(req,r);
      }
      else if(Resp===rp.EquipInfoListEquipRsp){
        r=localAutoWearEquipment(req,r);
      }
      else if(Resp===rp.EquipInfoListQueryRsp){
        r=localMakeEquipmentListRsp(req,r);
      }
      else if(Resp===rp.EquipInfoSpiritEquipQueryRsp){
        r=localMakeSpiritEquipmentRsp(req,r);
      }
      else if(Resp===rp.EquipDetailInfoQueryRsp){
        var detailUser=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
        var detailItem=localItemBySid(detailUser,req&&req.sid);
        r.ret=detailItem?0:1;
        r.equipInfo=detailItem?localMakeEquipDetail(detailItem,localEquipmentPosition(detailItem.id)):null;
        log("local equipment detail",Number(req&&req.sid),!!r.equipInfo);
      }
      else if(Resp===rp.EquipInfoChangeRsp){
        r=localApplyEquipmentChange(req,r);
      }
      else if(Resp===rp.PetFormationChangeRsp){
        r=makeOfflinePackMutation(req,"formationChange",r);
      }
      else if(Resp===rp.PetPackInfoSwapRsp){
        r=makeOfflinePackMutation(req,"packSwap",r);r.packInfo=current&&current.petPackInfo;
      }
      else if(Resp===rp.PetFormationSwapRsp){
        r=makeOfflinePackMutation(req,"formationSwap",r);r.packInfo=current&&current.petPackInfo;
      }
      else if(Resp===rp.TakePetFromStorageToPackRsp){
        r=makeOfflinePackMutation(req,"takePet",r);r.packInfo=current&&current.petPackInfo;r.storageInfo=current&&current.petStorageInfo;
      }
      else if(Resp===rp.CleanOnePackNodeRsp){
        r=makeOfflinePackMutation(req,"cleanPet",r);r.packInfo=current&&current.petPackInfo;r.storageInfo=current&&current.petStorageInfo;
      }
      else if(Resp===rp.NewTaskInfoOperateRsp){
        r=makeOfflineTaskOperate(req,r);
      }
      else if(Resp===rp.HangupOperateRsp){
        r=makeOfflineHangupRsp(req,r);
      }
      else if(Resp===rp.QuickHangupOperateRsp){
        r=makeOfflineQuickHangupRsp(req,r);
      }
      if(cb)setTimeout(function(){try{cb.call(ctx||null,r);}catch(e){log("response callback",e&&e.stack||e);}},0);
      return Promise.resolve(r);
    };
  }
  try{
    var crm=game.combat&&game.combat.CombatResManager&&game.combat.CombatResManager.prototype;
    if(crm&&!crm.__offlinePetPackGuard){
      var preloadCombatRes=crm.preloadCombatRes;
      crm.preloadCombatRes=function(){
        try{var u=DM.G().userInfo,slots=normalizePetPack(u);log("pet pack normalized before combat preload",slots.length,slots[0]&&!!slots[0].pet);}
        catch(e){log("pet pack normalization",e&&e.stack||e);}
        return preloadCombatRes.apply(this,arguments);
      };
      crm.__offlinePetPackGuard=true;
    }
  }catch(e){log("combat preload guard",e&&e.stack||e);}
  if(typeof game!=="undefined"&&game.module&&game.module.login){
    var L=game.module.login.LoginModule;
    L.prototype.prelogin=function(){this._isNewUser=false;this.currentZone={zone_id:1,user_id:UID,name:"本地离线服",status:1,repair:0};this.host="127.0.0.1";this.port=19999;DM.userID=long(UID);return Promise.resolve();};
    if(game.module.login.LoginUI){var ui=game.module.login.LoginUI.prototype,old=ui.getServerList;ui.getServerList=function(){old.call(this);var self=this;Laya.timer.once(350,this,function(){if(self.currentServerNode)self.onStartClick();});};}
  }
  try{
    var cardModel=mdl.CardCollect.CardCollectModel.prototype,cardInit=cardModel.init;
    cardModel.init=function(data){
      data=data||new rp.CardCollectInfo();
      if(!data.cards)data.cards={};if(!data.cardMails)data.cardMails=[];
      if(!data.taskProgress)data.taskProgress={};if(!data.buyLimit)data.buyLimit={};
      if(!data.cardGroupAwards)data.cardGroupAwards={};
      if(!data.nowSeason||!GC.G().CARD_COLLECT_SEASON_CONF.getDes(data.nowSeason))data.nowSeason=currentCardSeason();
      log("card collection initialized",data.nowSeason);
      return cardInit.call(this,data);
    };
    cardModel.getTime=function(){
      if(!this.data)this.data=new rp.CardCollectInfo();
      if(!this.data.nowSeason||!GC.G().CARD_COLLECT_SEASON_CONF.getDes(this.data.nowSeason))this.data.nowSeason=currentCardSeason();
      var cfg=GC.G().CARD_COLLECT_SEASON_CONF.getDes(this.data.nowSeason);
      if(!cfg){var now=Date.now()/1000;return [now-86400,now+86400];}
      this.getCurSeasonCardCfgs();return [cfg.startTime,cfg.endTime];
    };
  }catch(cardPatchError){log("card model patch",cardPatchError);}
  if(typeof DM!=="undefined"&&DM.G){var dm=DM.G(),change=dm.onUserInfoChange;dm.onUserInfoChange=function(e){var r=change&&change.call(this,e);save();return r;};}
  function ensure(){if(!current)current=userInfo();if(typeof DM!=="undefined"&&DM.G){DM.G().userInfo=current;DM.G().userLeadValue=[];DM.G().offineInfo=new rp.OffineLineInfo();DM.G().openSvrDays=20;DM.serverTime=Date.now();}save();}
  window.OfflineGame={
    version:1,save:save,
    getState:function(){var u=(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo)||current;return u&&u.baseInfo?{name:u.baseInfo.name,level:u.baseInfo.level,gold:String(u.baseInfo.moneyInfo.gold),diamond:u.baseInfo.moneyInfo.diamond,cash:u.baseInfo.moneyInfo.cash}:{};},
    addGold:function(n){ensure();var m=DM.G().userInfo.baseInfo.moneyInfo;m.gold=long(Number(m.gold||0)+Number(n||0));save();},
    addDiamond:function(n){ensure();var m=DM.G().userInfo.baseInfo.moneyInfo;m.diamond=Number(m.diamond||0)+Number(n||0);save();},
    addCash:function(n){ensure();var m=DM.G().userInfo.baseInfo.moneyInfo;m.cash=Number(m.cash||0)+Number(n||0);save();},
    addItem:function(id,count){ensure();addLocalItem(id,count);save();},
    selfTestPetStarUp:function(){
      ensure();
      var u=DM.G().userInfo,stored=u.petStorageInfo.petArray||[],start=stored.length;
      if(!localAddPetToStorage(u,1108,2,2,2)){
        log("local pet star-up self-test FAIL could not seed two pets");
        return {pass:false};
      }
      var entries=stored.slice(start).filter(function(pet){
        return pet&&Number(pet.id)===1108&&Number(pet.starLevel)===2;
      });
      if(entries.length!==2){
        log("local pet star-up self-test FAIL wrong seed count",entries.length);
        return {pass:false};
      }
      var req=new rp.PetStarLevelUpReq();
      req.petGenIds=entries.map(function(pet){return Number(pet.genId);});
      req.costGroups=entries.map(function(){return {costPetGenIds:[]};});
      var rsp=makeOfflinePetStarLevelUpRsp(req,new rp.PetStarLevelUpRsp());
      var results=entries.map(function(pet){return localPetOwnedRecord(u,pet.genId);});
      var ok=Number(rsp.ret)===0&&results.every(function(record){
        return record&&Number(record.pet.starLevel)===3&&Number(record.pet.hp)>1600&&
          Number(record.pet.attack)>620&&Number(record.pet.defense)>160;
      });
      log("local pet star-up self-test",ok?"PASS":"FAIL","ret",rsp.ret,
        "batch",entries.length,"stars",results.map(function(record){
          return Number(record&&record.pet&&record.pet.starLevel)||0;
        }).join(","));
      save();
      return {pass:ok,ret:rsp.ret,batch:entries.length,stars:results.map(function(record){
        return Number(record&&record.pet&&record.pet.starLevel)||0;
      })};
    },
    selfTestPetStarCard:function(){
      ensure();
      var u=DM.G().userInfo,target=u.petPackInfo.packArray[0]&&u.petPackInfo.packArray[0].pet;
      if(!target||Number(target.id)!==3101){
        log("local pet star-card self-test FAIL expected base pet 3101");
        return {pass:false};
      }
      if(Number(target.starLevel||0)>=6){
        log("local pet star-card self-test SKIP already star",Number(target.starLevel));
        return {pass:true,skipped:true};
      }
      if(Number(target.starLevel||0)!==5){
        log("local pet star-card self-test FAIL expected star 5",Number(target.starLevel));
        return {pass:false};
      }
      if(!localAddPetToStorage(u,3101,3,5,2)){
        log("local pet star-card self-test FAIL could not seed fodder");
        return {pass:false};
      }
      addLocalItem(1001159,1);
      addLocalItem(1001001,1000);
      var fodder=(u.petStorageInfo.petArray||[]).filter(function(pet){
        return pet&&Number(pet.id)===3101&&Number(pet.starLevel)===5&&
          String(pet.genId)!==String(target.genId);
      }).slice(-3);
      var beforeCard=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1001159]&&u.itemPackInfo.idMap[1001159].count||0),
        beforeMaterial=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1001001]&&u.itemPackInfo.idMap[1001001].count||0);
      var req=new rp.OnePetStarLevelUpReq();req.petGenIds=Number(target.genId);
      req.choiceCost=[
        {petGenIds:[],costCards:[{itemId:1001159,count:1}]},
        {petGenIds:fodder.map(function(pet){return Number(pet.genId);}),costCards:[]}
      ];
      var rsp=makeOfflineOnePetStarLevelUpRsp(req,new rp.OnePetStarLevelUpRsp());
      var afterCard=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1001159]&&u.itemPackInfo.idMap[1001159].count||0),
        afterMaterial=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1001001]&&u.itemPackInfo.idMap[1001001].count||0),
        remainingFodder=fodder.filter(function(pet){return !!localPetOwnedRecord(u,pet.genId);}).length;
      var ok=Number(rsp.ret)===0&&Number(target.starLevel)===6&&Number(target.hp)>13000&&
        beforeCard>=1&&afterCard===beforeCard-1&&beforeMaterial>=1000&&
        afterMaterial===beforeMaterial-1000&&remainingFodder===0;
      log("local pet star-card self-test",ok?"PASS":"FAIL","ret",rsp.ret,
        "star",5,"->",Number(target.starLevel)||0,
        "card",beforeCard,"->",afterCard,"material",beforeMaterial,"->",afterMaterial,
        "fodderRemaining",remainingFodder);
      save();
      return {pass:ok,ret:rsp.ret,star:Number(target.starLevel)||0,
        card:afterCard,material:afterMaterial,fodderRemaining:remainingFodder};
    },
    selfTestPetEvolution:function(){
      ensure();
      var u=DM.G().userInfo,packs=normalizePetPack(u),index=-1;
      for(var i=1;i<packs.length;i++)if(!packs[i]||!packs[i].pet){index=i;break;}
      if(index<0){log("local pet evolution self-test FAIL no free pack slot");return {pass:false};}
      var money=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo()),
        beforeGold=Number(money.gold||0);
      addLocalItem(1000019,500);
      var beforeStones=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1000019]&&u.itemPackInfo.idMap[1000019].count||0);
      var pet=petFrom({id:1108,genId:880001,level:2,starLevel:2});
      packs[index].pet=pet;packs[index].state=1;packs[index].combatPos=0;
      // Give the test pet a real configured item so evolution must preserve
      // and calculate the same equipment bonus as the original evolution UI.
      addLocalItem(4000002,1);
      var testHat=localEquipmentRecords(u).filter(function(rec){
        return rec.position===2&&Number(rec.owner)===0;
      }).slice(-1)[0];
      if(!testHat){
        log("local pet evolution self-test FAIL no free configured hat");
        return {pass:false};
      }
      packs[index].equip=[testHat.item];
      var beforeGear=localEquipmentBonusForNode(packs[index]);
      var req=new rp.PetGrowupEvolveReq();req.index=index;
      var rsp=makeOfflinePetGrowupEvolveRsp(req,new rp.PetGrowupEvolveRsp());
      var afterGold=Number(money.gold||0),
        afterStones=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1000019]&&u.itemPackInfo.idMap[1000019].count||0),
        afterGear=localEquipmentBonusForNode(packs[index]);
      var evolvedHp=Number(packs[index].pet&&packs[index].pet.hp)||0;
      var ok=Number(rsp.ret)===0&&Number(packs[index].pet&&packs[index].pet.id)===1208&&
        afterGold===beforeGold-10000&&beforeStones>=500&&afterStones===beforeStones-500&&
        Number(beforeGear.hp)===3125&&Number(afterGear.hp)===3125&&evolvedHp>6000;
      log("local pet evolution self-test",ok?"PASS":"FAIL","ret",rsp.ret,
        "pet",1108,"->",Number(packs[index].pet&&packs[index].pet.id)||0,
        "gold",beforeGold,"->",afterGold,"stones",beforeStones,"->",afterStones,
        "gearHp",Number(beforeGear.hp)||0,"->",Number(afterGear.hp)||0,
        "evolvedHp",evolvedHp);
      save();
      return {pass:ok,ret:rsp.ret,pet:Number(packs[index].pet&&packs[index].pet.id)||0,
        gold:afterGold,stones:afterStones};
    },
    selfTestHangup:function(){
      ensure();
      var u=DM.G().userInfo,stage=Number(u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneLevel)||1,
        next=offlineTaskConfig("NEW_SCENE_GRADE_CONF",stage+1),
        level=Number(next&&next.level)||1,cfg=offlineTaskConfig("HANGUP_DETAILS_CONF",level);
      if(!cfg||!Array.isArray(cfg.actionArr)||!cfg.actionArr.length){
        log("local hangup self-test FAIL missing configured rewards",stage,level);
        return {pass:false};
      }
      function fingerprint(){
        var money=u.baseInfo.moneyInfo||{},items=u.itemPackInfo&&u.itemPackInfo.idMap||{},
          storage=u.petStorageInfo&&u.petStorageInfo.petArray||[],points=u.baseInfo.newPointItemMap||{};
        return JSON.stringify({
          gold:String(money.gold||0),diamond:Number(money.diamond)||0,cash:Number(money.cash)||0,
          petCoin:String(money.petCoin||0),points:points,
          items:Object.keys(items).sort(function(a,b){return Number(a)-Number(b);}).map(function(id){
            return [id,Number(items[id]&&items[id].count)||0];
          }),
          pets:storage.map(function(p){return [Number(p&&p.genId)||0,Number(p&&p.id)||0];}),
          avatarBits:u.baseInfo.avatarBits||[]
        });
      }
      var now=Math.floor(Date.now()/1000);
      offlineTaskMeta.lastHangupTime=now-59;
      var shortTime=Number(offlineTaskMeta.lastHangupTime),beforeShort=fingerprint(),
        shortReq=new rp.HangupOperateReq();
      shortReq.operate=0;
      var shortQuery=makeOfflineHangupRsp(shortReq,new rp.HangupOperateRsp());
      var shortOk=Number(shortQuery.ret)===0&&Array.isArray(shortQuery.awards)&&
        shortQuery.awards.length===0&&Number(offlineTaskMeta.lastHangupTime)===shortTime&&
        fingerprint()===beforeShort;
      now=Math.floor(Date.now()/1000);
      offlineTaskMeta.lastHangupTime=now-3600;
      var queryTime=Number(offlineTaskMeta.lastHangupTime),beforeQuery=fingerprint(),
        queryReq=new rp.HangupOperateReq();
      queryReq.operate=0;
      var query=makeOfflineHangupRsp(queryReq,new rp.HangupOperateRsp());
      var queryOk=Number(query.ret)===0&&Array.isArray(query.awards)&&
        query.awards.length===cfg.actionArr.length&&query.awards.length>0&&
        Number(offlineTaskMeta.lastHangupTime)===queryTime&&fingerprint()===beforeQuery;
      var beforeClaim=fingerprint(),claimStarted=Math.floor(Date.now()/1000),
        claimsBefore=Number(offlineTaskMeta.dailyCounters[52])||0,
        claimReq=new rp.HangupOperateReq();
      claimReq.operate=1;
      var claim=makeOfflineHangupRsp(claimReq,new rp.HangupOperateRsp());
      var afterClaim=fingerprint(),claimsAfter=Number(offlineTaskMeta.dailyCounters[52])||0,
        claimOk=Number(claim.ret)===0&&Array.isArray(claim.awards)&&
          claim.awards.length===cfg.actionArr.length&&claim.awards.length>0&&
          Number(offlineTaskMeta.lastHangupTime)>=claimStarted&&
          claimsAfter===claimsBefore+1&&afterClaim!==beforeClaim;
      var duplicateReq=new rp.HangupOperateReq();duplicateReq.operate=1;
      var duplicate=makeOfflineHangupRsp(duplicateReq,new rp.HangupOperateRsp());
      var duplicateOk=Number(duplicate.ret)!==0&&
        (!duplicate.awards||duplicate.awards.length===0)&&
        fingerprint()===afterClaim&&
        (Number(offlineTaskMeta.dailyCounters[52])||0)===claimsAfter;
      var ok=shortOk&&queryOk&&claimOk&&duplicateOk;
      log("local hangup self-test",ok?"PASS":"FAIL",
        "query",query.ret,"claim",claim.ret,"duplicate",duplicate.ret,
        "under60",shortOk?"PASS":"FAIL",
        "level",level,"rewards",claim.awards&&claim.awards.length||0);
      offlineTaskMeta.expectedHangupRestoreTime=Number(offlineTaskMeta.lastHangupTime)||0;
      offlineTaskMeta.dayKey="1999-12-31";
      save();
      return {pass:ok,query:query.ret,claim:claim.ret,duplicate:duplicate.ret,
        rewards:claim.awards&&claim.awards.length||0};
    },
    selfTestQuickHangup:function(){
      ensure();
      var u=DM.G().userInfo,stage=Number(u.newSceneGradeInfo&&u.newSceneGradeInfo.sceneLevel)||1,
        next=offlineTaskConfig("NEW_SCENE_GRADE_CONF",stage+1),
        level=Number(next&&next.level)||1,cfg=offlineTaskConfig("HANGUP_DETAILS_CONF",level);
      if(!cfg||!Array.isArray(cfg.actionArr)||!cfg.actionArr.length){
        log("local quick hangup self-test FAIL missing configured rewards",stage,level);
        return {pass:false};
      }
      function fingerprint(){
        var money=u.baseInfo.moneyInfo||{},items=u.itemPackInfo&&u.itemPackInfo.idMap||{},
          points=u.baseInfo.newPointItemMap||{};
        return JSON.stringify({
          gold:String(money.gold||0),diamond:Number(money.diamond)||0,cash:Number(money.cash)||0,
          petExp:Number(points[56])||0,userExp:Number(points[4])||0,intelligence:Number(points[59])||0,
          items:Object.keys(items).sort(function(a,b){return Number(a)-Number(b);}).map(function(id){
            return [id,Number(items[id]&&items[id].count)||0];
          })
        });
      }
      quickCombatUsed=0;
      var beforeQuery=fingerprint(),queryReq=new rp.QuickHangupOperateReq();
      queryReq.operate=0;
      var query=makeOfflineQuickHangupRsp(queryReq,new rp.QuickHangupOperateRsp());
      var queryOk=Number(query.ret)===0&&query.todayUseCount===0&&query.maxDayUseCount===1&&
        query.awards.length===cfg.actionArr.length&&fingerprint()===beforeQuery;
      var beforeClaim=fingerprint(),claimsBefore=Number(offlineTaskMeta.dailyCounters[49])||0,
        claimReq=new rp.QuickHangupOperateReq();
      claimReq.operate=1;
      var claim=makeOfflineQuickHangupRsp(claimReq,new rp.QuickHangupOperateRsp());
      var afterClaim=fingerprint(),claimsAfter=Number(offlineTaskMeta.dailyCounters[49])||0;
      var claimOk=Number(claim.ret)===0&&claim.todayUseCount===1&&
        claim.awards.length===cfg.actionArr.length&&afterClaim!==beforeClaim&&
        claimsAfter===claimsBefore+1;
      var duplicateReq=new rp.QuickHangupOperateReq();duplicateReq.operate=1;
      var duplicate=makeOfflineQuickHangupRsp(duplicateReq,new rp.QuickHangupOperateRsp());
      var duplicateOk=Number(duplicate.ret)===1&&duplicate.awards.length===0&&
        fingerprint()===afterClaim&&quickCombatUsed===1;
      var cashBefore=Number(u.baseInfo.moneyInfo&&u.baseInfo.moneyInfo.cash)||0,
        paidReq=new rp.QuickHangupOperateReq();paidReq.operate=2;
      var paid=makeOfflineQuickHangupRsp(paidReq,new rp.QuickHangupOperateRsp());
      var paidOk=Number(paid.ret)===1&&paid.awards.length===0&&
        (Number(u.baseInfo.moneyInfo&&u.baseInfo.moneyInfo.cash)||0)===cashBefore;
      var ok=queryOk&&claimOk&&duplicateOk&&paidOk;
      log("local quick hangup self-test",ok?"PASS":"FAIL",
        "query",query.ret,"claim",claim.ret,"duplicate",duplicate.ret,"paid",paid.ret,
        "rewards",claim.awards&&claim.awards.length||0);
      save();
      return {pass:ok,query:query.ret,claim:claim.ret,duplicate:duplicate.ret,paid:paid.ret};
    },
    selfTestPetCrystal:function(){
      ensure();
      var u=DM.G().userInfo,info=localRefreshPetCrystal(u),
        money=u.baseInfo.moneyInfo||(u.baseInfo.moneyInfo=new rp.MoneyInfo()),
        beforeCash=Number(money.cash||0),already=info.slotInfo&&info.slotInfo[7];
      if(already&&Number(already.slotType)>0){
        log("local pet crystal self-test SKIP slot7 already unlocked");
        return {pass:true,skipped:true};
      }
      // Slot 7 offers two alternative payments; costType 0 selects the 200-cash option.
      var beforeStones=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1001004]&&u.itemPackInfo.idMap[1001004].count||0);
      var unlockReq=new rp.PetCrystalUnlockReq();unlockReq.index=7;unlockReq.costType=0;
      var unlock=makeOfflinePetCrystalUnlockRsp(unlockReq,new rp.PetCrystalUnlockRsp());
      var slot=info.slotInfo&&info.slotInfo[7];
      var pet=u.petPackInfo.packArray[0]&&u.petPackInfo.packArray[0].pet;
      var placed=null,removed=null,cleared=null;
      if(Number(unlock.ret)===0&&pet&&Number(pet.genId)>0){
        var setReq=new rp.PetCrystalSetReq();setReq.index=7;setReq.genId=Number(pet.genId);
        placed=makeOfflinePetCrystalSetRsp(setReq,new rp.PetCrystalSetRsp());
        var getReq=new rp.PetCrystalGetReq();getReq.index=7;
        removed=makeOfflinePetCrystalGetRsp(getReq,new rp.PetCrystalGetRsp());
        var buyReq=new rp.PetCrystalBuyCoolTimeReq();buyReq.index=7;
        cleared=makeOfflinePetCrystalBuyCoolTimeRsp(buyReq,new rp.PetCrystalBuyCoolTimeRsp());
      }
      var afterCash=Number(money.cash||0),
        afterStones=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1001004]&&u.itemPackInfo.idMap[1001004].count||0);
      var ok=Number(unlock.ret)===0&&Number(placed&&placed.ret)===0&&
        Number(removed&&removed.ret)===0&&Number(cleared&&cleared.ret)===0&&
        afterCash===beforeCash-200-96&&afterStones===beforeStones&&
        slot&&Number(slot.slotType)===Number(rp.PetCrystalSlot.Type.Unlock);
      log("local pet crystal self-test",ok?"PASS":"FAIL",
        "unlock",unlock.ret,"set",placed&&placed.ret,"get",removed&&removed.ret,
        "cooldownClear",cleared&&cleared.ret,"slot7",Number(slot&&slot.slotType)||0,
        "cash",beforeCash,"->",afterCash,"stones",beforeStones,"->",afterStones);
      save();
      return {pass:ok,unlock:unlock.ret,set:placed&&placed.ret,get:removed&&removed.ret,
        clear:cleared&&cleared.ret,cash:afterCash,stones:afterStones};
    },
    selfTestItemUse:function(){
      ensure();
      var u=DM.G().userInfo,initialGold=Number(u.baseInfo.moneyInfo&&u.baseInfo.moneyInfo.gold||0),
        initialPetExp=Number(u.baseInfo.newPointItemMap&&u.baseInfo.newPointItemMap[5]||0),
        initialComposed=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[3000002]&&u.itemPackInfo.idMap[3000002].count||0),
        initialDecomposed=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1000590]&&u.itemPackInfo.idMap[1000590].count||0);
      function run(id,useType,count,index){
        addLocalItem(id,count);
        var req=new rp.UseItemReq();req.id=id;req.useType=useType;req.count=count;req.index=index||0;
        return makeOfflineUseItemRsp(req,new rp.UseItemRsp());
      }
      var sell=run(1000006,Number(rp.UseItemReq.UseType.USETYPE_SELL),1,0);
      var use=run(1001011,Number(rp.UseItemReq.UseType.USETYPE_USE),1,0);
      var compose=run(3000001,Number(rp.UseItemReq.UseType.USETYPE_COMPOSE),2,0);
      addLocalItem(3000001,1);
      var decomposeReq=new rp.UseItemReq();decomposeReq.id=3000001;
      decomposeReq.useType=Number(rp.UseItemReq.UseType.USETYPE_DECOMPOSE);decomposeReq.count=1;
      var decompose=makeOfflineUseItemRsp(decomposeReq,new rp.UseItemRsp());
      var finalGold=Number(u.baseInfo.moneyInfo&&u.baseInfo.moneyInfo.gold||0),
        finalPetExp=Number(u.baseInfo.newPointItemMap&&u.baseInfo.newPointItemMap[5]||0),
        composed=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[3000002]&&u.itemPackInfo.idMap[3000002].count||0),
        decomposed=Number(u.itemPackInfo.idMap&&u.itemPackInfo.idMap[1000590]&&u.itemPackInfo.idMap[1000590].count||0);
      var ok=Number(sell.ret)===0&&Number(use.ret)===0&&Number(compose.ret)===0&&Number(decompose.ret)===0&&
        finalGold===initialGold+1&&finalPetExp>initialPetExp&&
        composed===initialComposed+1&&decomposed===initialDecomposed+1;
      log("local item operations self-test",ok?"PASS":"FAIL","sell",sell.ret,"use",use.ret,
        "compose",compose.ret,"decompose",decompose.ret,"gold",initialGold,"->",finalGold,
        "petExp",initialPetExp,"->",finalPetExp,"composed",composed,"decomposed",decomposed);
      save();
      return {pass:ok,sell:sell.ret,use:use.ret,compose:compose.ret,decompose:decompose.ret,
        gold:finalGold,petExp:finalPetExp,composed:composed,decomposed:decomposed};
    },
    useItem:function(id,useType,count,index,sid){
      ensure();
      var req=new rp.UseItemReq();req.id=Number(id)||0;req.useType=Number(useType)||0;
      req.count=Math.max(1,Math.floor(Number(count)||1));req.index=Number(index)||0;
      if(sid!=null)req.sid=localLongValue(sid);
      return Promise.resolve(makeOfflineUseItemRsp(req,new rp.UseItemRsp()));
    },
    saveAndNotify:function(){ensure();try{var e=new rp.EntireNotify();e.userBaseInfo=DM.G().userInfo.baseInfo;DM.G().onUserInfoChange(e);}catch(x){}save();},
    reset:function(){localStorage.removeItem(KEY);location.reload();},
    bots:bots().map(function(x){return {name:x.name,level:x.level,offline:true};}),
    returnToAdventure:function(){
      try{
        var combat=typeof game!=="undefined"&&game.combat&&game.combat.Combat&&game.combat.Combat.getInstance();
        var winClass=typeof game!=="undefined"&&game.combat&&game.combat.CombatWinUI1;
        var panelClass=typeof mdl!=="undefined"&&mdl.Checkpoint&&mdl.Checkpoint.MainChallenge;
        var manager=typeof PM!=="undefined"&&PM.G&&PM.G(),panels=manager&&manager.panelList||[];
        function findWin(root){
          if(!root)return null;
          if(winClass&&root instanceof winClass)return root;
          var count=Number(root.numChildren)||0;
          for(var k=0;k<count;k++){var found=findWin(root.getChildAt(k));if(found)return found;}
          return null;
        }
        var winPanel=null;
        for(var i=panels.length-1;i>=0&&!winPanel;i--)winPanel=findWin(panels[i]);
        if(combat&&combat.duringCombat&&!winPanel){
          log("local return to adventure blocked: battle has no result panel yet");
          return false;
        }
        if(winPanel){
          if(typeof winPanel.onClose==="function"){
            winPanel.onClose();
            log("local return to adventure closed CombatWinUI1");
          }else{
            log("local return to adventure result panel has no close handler");
            return false;
          }
        }
        panels=manager&&manager.panelList||[];
        for(var j=panels.length-1;j>=0;j--){
          var panel=panels[j];
          if(panelClass&&panel instanceof panelClass){
            if(typeof panel.onClose==="function")panel.onClose();
            else manager.closePanel(panel);
            log("local return to adventure closed MainChallenge");
            return true;
          }
        }
        if(winPanel)return true;
        log("local return to adventure MainChallenge panel not found");
      }catch(e){log("local return to adventure error",e&&e.stack||e);}
      return false;
    },
    openTasks:function(tab){
      try{
        ensure();
        if(typeof mdl!=="undefined"&&mdl.Task&&mdl.Task.Entry){
          var tabCount=3;
          try{if(util.UOther.getOpen(93).flag&&!DM.isLimitCity)tabCount=4;}catch(_){}
          log("local task panel tabs",tabCount);
          mdl.Task.Entry.show(Number(tab)||1);
          log("local task panel opened",Number(tab)||1);
          return true;
        }
      }catch(e){log("local task panel open error",e&&e.stack||e);}
      return false;
    }
  };
  try{
    var challenge=typeof mdl!=="undefined"&&mdl.Checkpoint&&mdl.Checkpoint.MainChallengeStatic;
    if(challenge&&typeof challenge.openCombat==="function"&&!challenge.__offlineCompletionHook){
      var originalOpenCombat=challenge.openCombat;
      challenge.openCombat=function(){
        var completedLevel=Number(this.fightRsp&&this.fightRsp.sceneLevel)||Number(this.level)||0;
        var hadSequence=!!(this.fightRsp&&this.fightData);
        var result=originalOpenCombat.apply(this,arguments);
        if(hadSequence&&this.fightRsp==null&&this.fightData==null)
          log("local main challenge sequence complete",completedLevel);
        return result;
      };
      challenge.__offlineCompletionHook=true;
    }
  }catch(e){log("local main challenge completion hook",e&&e.stack||e);}
  try{
    var combatUIClass=typeof game!=="undefined"&&game.combat&&game.combat.CombatUI;
    if(combatUIClass&&combatUIClass.prototype&&typeof combatUIClass.prototype.onCombatDone==="function"&&!combatUIClass.prototype.__offlineResultHook){
      var originalCombatDone=combatUIClass.prototype.onCombatDone;
      combatUIClass.prototype.onCombatDone=function(){
        var result=originalCombatDone.apply(this,arguments),self=this;
        if(Number(this.winType)===Number(game.combat.winType.MainChallenge)){
          var deadline=Date.now()+15000;
          var findResult=function(){
            if(!self||self.destroyed||!self.parent)return;
            var resultClass=game.combat.CombatWinUI1,found=false;
            if(resultClass)for(var i=0;i<(Number(self.numChildren)||0);i++){
              var child=self.getChildAt(i);
              if(child instanceof resultClass){found=true;break;}
            }
            if(found)log("local main challenge result panel ready",Number(DM.G().userInfo.newSceneGradeInfo.sceneLevel)||0);
            else if(Date.now()<deadline)setTimeout(findResult,250);
          };
          setTimeout(findResult,250);
        }
        return result;
      };
      combatUIClass.prototype.__offlineResultHook=true;
    }
  }catch(e){log("local main challenge result hook",e&&e.stack||e);}
  setInterval(save,15000);window.addEventListener("beforeunload",save);log("offline patch installed");
})();
"""

OVERLAY = """
<style id="offline-menu-style">
#offline-menu-button{position:fixed;z-index:2147483646;left:10px;top:5px;padding:4px 6px;border-radius:8px;background:rgba(17,25,46,.9);border:1px solid #64c8ff;color:#fff;font:11px sans-serif}
#offline-task-button{position:fixed;z-index:2147483646;right:10px;top:5px;padding:4px 8px;border-radius:8px;background:rgba(17,25,46,.92);border:1px solid #ffe08a;color:#fff;font:12px sans-serif}
#offline-return-button{position:fixed;z-index:2147483648;left:10px;top:42px;padding:4px 8px;border-radius:8px;background:rgba(17,25,46,.92);border:1px solid #72e0a0;color:#fff;font:12px sans-serif}
#offline-menu-panel{position:fixed;z-index:2147483647;left:10px;top:42px;width:220px;padding:12px;border-radius:12px;background:rgba(12,18,36,.97);border:1px solid #64c8ff;color:#fff;font:14px sans-serif;display:none}
#offline-menu-panel h3{margin:0 0 8px;font-size:16px;color:#8de2ff}
#offline-menu-panel .stat{font-size:12px;line-height:1.6;margin-bottom:8px;color:#d6edff}
#offline-menu-panel button{width:100%;margin:4px 0;padding:8px;border:0;border-radius:8px;background:#287bb6;color:#fff;font-size:13px}
#offline-menu-panel .danger{background:#9e3946}.offline-note{font-size:11px;color:#ffdd9c;margin-top:7px;line-height:1.4}
</style>
<div id="offline-menu-button">离线菜单</div>
<div id="offline-task-button">任务</div>
<div id="offline-return-button">返回主城</div>
<div id="offline-menu-panel"><h3>超级精灵球 · 离线工具</h3><div id="offline-stat" class="stat">本地存档加载中…</div>
<button data-act="tasks">打开任务面板</button><button data-act="item-test">验证道具使用</button><button data-act="crystal-test">验证精灵水晶</button><button data-act="star-test">验证精灵升星</button><button data-act="star-card-test">验证魂灵卡升星</button><button data-act="evolution-test">验证精灵进化</button><button data-act="hangup-test">验证离线挂机</button><button data-act="quick-hangup-test">验证快速挂机</button><button data-act="gold">金币 +100万</button><button data-act="diamond">钻石 +1万</button><button data-act="cash">点券 +1万</button><button data-act="save">立即保存</button><button data-act="return-main">返回主城地图</button><button data-act="reset" class="danger">重置本地存档</button>
<div class="offline-note">模拟训练师为本地虚构数据，不连接在线排行榜；离线解锁不涉及真实支付。</div></div>
<script>
(function(){var n=0,t=setInterval(function(){n++;if(!window.OfflineGame&&n<120)return;clearInterval(t);var b=document.getElementById("offline-menu-button"),p=document.getElementById("offline-menu-panel"),s=document.getElementById("offline-stat"),tb=document.getElementById("offline-task-button"),rb=document.getElementById("offline-return-button");if(!b||!p)return;
if(tb)tb.onclick=function(){if(window.OfflineGame)OfflineGame.openTasks(1);};
if(rb)rb.onclick=function(){if(window.OfflineGame)OfflineGame.returnToAdventure();};
b.onclick=function(){p.style.display=p.style.display==="block"?"none":"block";if(window.OfflineGame)s.textContent=JSON.stringify(OfflineGame.getState());};
p.onclick=function(e){var a=e.target&&e.target.getAttribute("data-act");if(!a||!window.OfflineGame)return;try{if(a==="tasks")OfflineGame.openTasks(1);if(a==="item-test")OfflineGame.selfTestItemUse();if(a==="crystal-test")OfflineGame.selfTestPetCrystal();if(a==="star-test")OfflineGame.selfTestPetStarUp();if(a==="star-card-test")OfflineGame.selfTestPetStarCard();if(a==="evolution-test")OfflineGame.selfTestPetEvolution();if(a==="hangup-test")OfflineGame.selfTestHangup();if(a==="quick-hangup-test")OfflineGame.selfTestQuickHangup();if(a==="gold")OfflineGame.addGold(1000000);if(a==="diamond")OfflineGame.addDiamond(10000);if(a==="cash")OfflineGame.addCash(10000);if(a==="save")OfflineGame.saveAndNotify();if(a==="return-main"){OfflineGame.returnToAdventure();p.style.display="none";}if(a==="reset"&&confirm("确定清除本设备的离线存档吗？"))OfflineGame.reset();s.textContent=JSON.stringify(OfflineGame.getState());}catch(x){console.error(x);}};
},250);})();
</script>
"""

def patch(root: Path) -> None:
    index, code = root/"index.html", root/"code.js"
    if not index.is_file() or not code.is_file():
        raise SystemExit("index.html/code.js missing")
    html=index.read_text(encoding="utf-8",errors="replace")
    html=html.replace('<script src="https://res.wx.qq.com/open/js/jweixin-1.6.0.js"></script>','')
    bridge='<script>var CallbackFromAndroid=window.CallbackFromAndroid=window.CallbackFromAndroid||function(){};var CallbackFromIOS=window.CallbackFromIOS=window.CallbackFromIOS||function(){};</script>'
    html=html.replace(bridge,'')
    html=html.replace('<html>','<html>\n'+bridge,1)
    html=html.replace("https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/libQuickSDKH5_To_Client.js","./libQuickSDKH5_To_Client.js")
    if "offline-menu-button" not in html:
        html=html.replace("</body>",OVERLAY+"\n</body>")
    index.write_text(html,encoding="utf-8")
    # The loading page CSS points at a root bg3.jpg, while the server stores it under atlas/loading.
    import shutil
    if not (root/"bg3.jpg").is_file() and (root/"atlas/loading/bg3.jpg").is_file():
        shutil.copy2(root/"atlas/loading/bg3.jpg",root/"bg3.jpg")
    # The original currency icon is packed in common.atlas; the archived UI also
    # requests it as a loose image, so package the exact frame from that atlas.
    icon_source=Path(__file__).resolve().parents[1]/"assets"/"zuan01.png"
    icon_target=root/"res"/"icons"/"zuan01.png"
    if not icon_source.is_file():
        raise SystemExit("recovered zuan01.png atlas frame is missing")
    icon_target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(icon_source,icon_target)
    text=code.read_text(encoding="utf-8",errors="replace")
    sentinel="new GameShell;"
    if text.count(sentinel)!=1:
        raise SystemExit(f"expected one GameShell sentinel, got {text.count(sentinel)}")
    if "SUPER_SPIRIT_BALL_OFFLINE_PATCH_V1" not in text:
        text=text.replace(sentinel,HOOK+"\n"+sentinel)
    code.write_text(text,encoding="utf-8")

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("client_dir",type=Path)
    args=ap.parse_args();patch(args.client_dir)
    print("offline H5 patch applied:",args.client_dir)
