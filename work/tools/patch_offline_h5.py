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
  if(offlineDayReset){offlineTaskMeta.dayKey=offlineToday;offlineTaskMeta.dailyCounters={};offlineTaskMeta.lastHangupTime=Math.floor(Date.now()/1000)-3600;}
  if(offlineWeekReset){offlineTaskMeta.weekKey=offlineWeek;offlineTaskMeta.weeklyCounters={};}
  if(!offlineTaskMeta.dailyCounters)offlineTaskMeta.dailyCounters={};
  if(!offlineTaskMeta.weeklyCounters)offlineTaskMeta.weeklyCounters={};
  if(!offlineTaskMeta.lastHangupTime)offlineTaskMeta.lastHangupTime=Math.floor(Date.now()/1000)-3600;
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
    log("local equipment inventory query",type,r.equipInfoList.length);
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
    if(changed)save();
    var gearBonus=localEquipmentBonusForNode(node);
    log("local equipment auto-wear",slot+1,"equipped",equipped.length,
      "positions",selectedPositions.join(","),
      "bonus",Number(gearBonus.hp)||0,Number(gearBonus.attack)||0,Number(gearBonus.defense)||0);
    return r;
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
    }else if(type===Number(rp.Action.ActionTye.ADD_POINT_ITEM)||type===Number(rp.Action.ActionTye.ADD_LEVEL_EXP)){
      addLocalPointItem(p[0],p[1]);
    }
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
      if(!current.extInfo)current.extInfo=new rp.UserExtInfo();
      if(!current.extInfo.newGuildInfo)current.extInfo.newGuildInfo=new rp.NewGuildInfo();
      current.extInfo.newGuildInfo.version=0;current.extInfo.newGuildInfo.steps=current.extInfo.newGuildInfo.steps||{};
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
      else if(Resp===rp.PetGrowupExpRsp){
        r=makeOfflinePetGrowupRsp(req,r);
      }
      else if(Resp===rp.GetPetStorageRsp){
        r=makeOfflinePetStorageRsp(r);
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
        var usedBefore=quickCombatUsed,operate=Number(req&&req.operate||0);
        if(operate===1&&quickCombatUsed<1){
          quickCombatUsed++;addLocalGold(10000);
          offlineTaskMeta.dailyCounters[49]=(Number(offlineTaskMeta.dailyCounters[49])||0)+1;
          syncOfflineTaskProgress(current);
          save();
        }
        r.ret=(operate===2||(operate===1&&usedBefore>=1))?1:0;
        r.todayUseCount=quickCombatUsed;r.maxDayUseCount=1;
        r.todayBuyCount=0;r.maxDayBuyCount=0;
        r.awards=r.ret===0&&operate===1?[offlineAction(rp.Action.ActionTye.ADD_GOLD,[10000])]:[];
        log("local QuickHangupOperateRsp",operate,"used",quickCombatUsed);
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
    saveAndNotify:function(){ensure();try{var e=new rp.EntireNotify();e.userBaseInfo=DM.G().userInfo.baseInfo;DM.G().onUserInfoChange(e);}catch(x){}save();},
    reset:function(){localStorage.removeItem(KEY);location.reload();},
    bots:bots().map(function(x){return {name:x.name,level:x.level,offline:true};}),
    openTasks:function(tab){
      try{
        ensure();
        if(typeof mdl!=="undefined"&&mdl.Task&&mdl.Task.Entry){
          mdl.Task.Entry.show(Number(tab)||1);
          log("local task panel opened",Number(tab)||1);
          return true;
        }
      }catch(e){log("local task panel open error",e&&e.stack||e);}
      return false;
    }
  };
  setInterval(save,15000);window.addEventListener("beforeunload",save);log("offline patch installed");
})();
"""

OVERLAY = """
<style id="offline-menu-style">
#offline-menu-button{position:fixed;z-index:2147483646;right:100px;top:5px;padding:4px 6px;border-radius:8px;background:rgba(17,25,46,.9);border:1px solid #64c8ff;color:#fff;font:11px sans-serif}
#offline-task-button{position:fixed;z-index:2147483646;right:10px;top:5px;padding:4px 8px;border-radius:8px;background:rgba(17,25,46,.92);border:1px solid #ffe08a;color:#fff;font:12px sans-serif}
#offline-menu-panel{position:fixed;z-index:2147483647;right:10px;top:42px;width:220px;padding:12px;border-radius:12px;background:rgba(12,18,36,.97);border:1px solid #64c8ff;color:#fff;font:14px sans-serif;display:none}
#offline-menu-panel h3{margin:0 0 8px;font-size:16px;color:#8de2ff}
#offline-menu-panel .stat{font-size:12px;line-height:1.6;margin-bottom:8px;color:#d6edff}
#offline-menu-panel button{width:100%;margin:4px 0;padding:8px;border:0;border-radius:8px;background:#287bb6;color:#fff;font-size:13px}
#offline-menu-panel .danger{background:#9e3946}.offline-note{font-size:11px;color:#ffdd9c;margin-top:7px;line-height:1.4}
</style>
<div id="offline-menu-button">离线菜单</div>
<div id="offline-task-button">任务</div>
<div id="offline-menu-panel"><h3>超级精灵球 · 离线工具</h3><div id="offline-stat" class="stat">本地存档加载中…</div>
<button data-act="tasks">打开任务面板</button><button data-act="gold">金币 +100万</button><button data-act="diamond">钻石 +1万</button><button data-act="cash">点券 +1万</button><button data-act="save">立即保存</button><button data-act="reset" class="danger">重置本地存档</button>
<div class="offline-note">模拟训练师为本地虚构数据，不连接在线排行榜；离线解锁不涉及真实支付。</div></div>
<script>
(function(){var n=0,t=setInterval(function(){n++;if(!window.OfflineGame&&n<120)return;clearInterval(t);var b=document.getElementById("offline-menu-button"),p=document.getElementById("offline-menu-panel"),s=document.getElementById("offline-stat"),tb=document.getElementById("offline-task-button");if(!b||!p)return;
if(tb)tb.onclick=function(){if(window.OfflineGame)OfflineGame.openTasks(1);};
b.onclick=function(){p.style.display=p.style.display==="block"?"none":"block";if(window.OfflineGame)s.textContent=JSON.stringify(OfflineGame.getState());};
p.onclick=function(e){var a=e.target&&e.target.getAttribute("data-act");if(!a||!window.OfflineGame)return;try{if(a==="tasks")OfflineGame.openTasks(1);if(a==="gold")OfflineGame.addGold(1000000);if(a==="diamond")OfflineGame.addDiamond(10000);if(a==="cash")OfflineGame.addCash(10000);if(a==="save")OfflineGame.saveAndNotify();if(a==="reset"&&confirm("确定清除本设备的离线存档吗？"))OfflineGame.reset();s.textContent=JSON.stringify(OfflineGame.getState());}catch(x){console.error(x);}};
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
