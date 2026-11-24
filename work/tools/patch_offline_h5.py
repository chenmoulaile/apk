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
  var quickCombatUsed=Number(saved.quickCombatUsed)||0;
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
  function addLocalItem(id,amount){
    try{
      var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
      if(!u)return;
      if(!u.itemPackInfo)u.itemPackInfo=new rp.ItemPackInfo();
      if(!u.itemPackInfo.idMap)u.itemPackInfo.idMap={};
      id=Number(id);amount=Number(amount)||0;
      var item=u.itemPackInfo.idMap[id];
      if(!item)item=u.itemPackInfo.idMap[id]=new rp.ItemBase();
      item.id=id;item.count=Math.max(0,Number(item.count)||0)+amount;
      try{
        if(typeof DM!=="undefined"&&DM.G){
          var dm=DM.G();
          dm.itemIdMap=dm.itemIdMap||{};dm.itemIdMap[id]=item;
          if(Array.isArray(dm.itemPackInfos)){
            var at=dm.itemPackInfos.findIndex(function(x){return x&&Number(x.id)===id;});
            if(at<0)dm.itemPackInfos.push(item);else dm.itemPackInfos[at]=item;
          }
        }
      }catch(_){}
      log("local item reward",id,amount,item.count);
    }catch(e){log("local item update",e&&e.stack||e);}
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
    log("local pet growup",index,oldLevel+"->"+pet.level,"hp",String(pet.hp),"attack",String(pet.attack),"defense",String(pet.defense),
      "score",String(pet.fightScore),"gold",String(u.baseInfo.moneyInfo&&u.baseInfo.moneyInfo.gold||0),"point56",Number(u.baseInfo.newPointItemMap&&u.baseInfo.newPointItemMap[56]||0));
    save();return r;
  }
  function combatSpirit(id,level,hp){
    var s=new rp.CombatSpirit();
    s.id=id||0;s.level=level||1;s.status=id?rp.CombatSpiritStatus.ALIVE:rp.CombatSpiritStatus.UNKNOW;
    s.hp=long(id?hp||12000:0);s.fullHp=long(id?hp||12000:0);s.oldHp=id?hp||12000:0;
    s.mp=50;s.buffMap={};return s;
  }
  function combatPlayer(id,name,petId,level){
    var p=new rp.CombatPlayer();p.id=(Number(id)===0?0:long(id));p.name=name;p.level=level||1;p.sex=2;
    p.commuSkillId=0;p.warCmdLevel=0;p.warCmdSkill=0;p.godSkill=false;
    p.partner=[combatSpirit(0,1,0)];p.spirits=[];
    for(var i=0;i<6;i++)p.spirits.push(i===0?combatSpirit(petId,level,16000):combatSpirit(0,1,0));
    return p;
  }
  function makeOfflineCombat(stage){
    var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);
    var myPet=u&&u.petPackInfo&&u.petPackInfo.packArray&&u.petPackInfo.packArray[0]&&u.petPackInfo.packArray[0].pet;
    var myPetId=myPet&&myPet.id||3101;
    var myLevel=myPet&&myPet.level||1;
    var data=new rp.OneCombatData();data.type=rp.CombatType.PVE;data.result=rp.CombatResult.WIN;
    data.players=[
      combatPlayer(u&&u.baseInfo&&u.baseInfo.userId||UID,u&&u.baseInfo&&u.baseInfo.name||NAME,myPetId,myLevel),
      combatPlayer(0,"离线训练对手",3108,1)
    ];
    var begin=new rp.CombatOneStep();begin.doWhat=rp.CombatStepType.START;begin.round=1;begin.source=0;
    var finish=new rp.CombatOneStep();finish.doWhat=rp.CombatStepType.END;finish.round=1;finish.source=0;
    data.steps=[begin,finish];data.totalRound=1;data.time=3;data.rewards=[];
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
    var result=new rp.NewSceneResultInfo();result.sceneLevel=nextLevel;
    result.fightData=[makeOfflineCombat(nextLevel)];rsp.fightInfo=[result];
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
    u.itemPackInfo=new rp.ItemPackInfo();u.petPackInfo=new rp.PetPackInfo();u.petStorageInfo=new rp.PetStorageInfo();
    var prior=saved.petPackInfo&&saved.petPackInfo.packArray&&saved.petPackInfo.packArray[0]&&saved.petPackInfo.packArray[0].pet;
    var p=petFrom(prior),packs=[];for(var i=0;i<18;i++){var n=new rp.PackNode();n.index=i+1;n.state=i===0?1:0;n.equip=[];if(i===0){n.pet=p;n.combatPos=1;}packs.push(n);}
    u.petPackInfo.packArray=packs;u.petStorageInfo.petArray=[p];u.petStorageInfo.sidGenerator=100002;
    u.sceneBagInfo=new rp.SceneBagInfo();u.sceneBagInfo.sceneBag=new rp.SceneStorageBag();u.sceneBagInfo.limitInfo=new rp.SceneLimitInfo();
    u.redotInfo=new rp.RedotInfo();u.activityInfo=new rp.ActivityInfo();u.petRoomInfo=new rp.PetRoomInfo();u.happyBeachInfo=new rp.HappyBeachInfo();
    u.newSceneGradeInfo=new rp.NewSceneGradeInfo();u.newSceneGradeInfo.sceneLevel=1;u.newSceneGradeInfo.sceneMapId=1;
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
    return u;
  }
  function save(){
    try{var u=current||(typeof DM!=="undefined"&&DM.G&&DM.G().userInfo);if(!u||!u.baseInfo)return;
      var p=u.petPackInfo&&u.petPackInfo.packArray&&u.petPackInfo.packArray[0]&&u.petPackInfo.packArray[0].pet,m=u.baseInfo.moneyInfo;
      var x={version:4,quickCombatUsed:quickCombatUsed,userInfo:{baseInfo:{userId:String(u.baseInfo.userId),name:u.baseInfo.name,sex:u.baseInfo.sex,level:u.baseInfo.level,vipLevel:u.baseInfo.vipLevel,sceneLevel:u.baseInfo.sceneLevel,avatarId:u.baseInfo.avatarId,
        newPointItemMap:u.baseInfo.newPointItemMap||{},
        moneyInfo:{gold:String(m.gold||0),diamond:m.diamond||0,cash:m.cash||0,petCoin:String(m.petCoin||0),equipCoin:String(m.equipCoin||0),warScoreCoin:String(m.warScoreCoin||0),honorCoin:String(m.honorCoin||0),rankGameScore:m.rankGameScore||0}}},
        petPackInfo:{packArray:[{pet:p?{id:p.id,level:p.level,genId:p.genId,name:p.name,exp:p.exp,hp:String(p.hp||0),attack:String(p.attack||0),defense:String(p.defense||0),fightScore:String(p.fightScore||0),starLevel:p.starLevel,insight:p.insight,washHp:p.washHp,washAttack:p.washAttack,washDefense:p.washDefense}:null}]}};
      try{var bytes=rp.UserDataInfo.encode(u).finish(),binary="";for(var i=0;i<bytes.length;i++)binary+=String.fromCharCode(bytes[i]);x.proto=btoa(binary);}
      catch(protoError){log("protobuf save fallback",protoError);}
      var persisted={version:x.version,quickCombatUsed:quickCombatUsed,userInfo:x.userInfo,petPackInfo:x.petPackInfo};if(x.proto)persisted.proto=x.proto;
      localStorage.setItem(KEY,JSON.stringify(persisted));x.restored=u;saved=x;
    }catch(e){log("save error",e);}
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
        r.ret=0;r.attr=new rp.PkAttrInfo();r.teamPkAttr=new rp.PkAttrInfo();
        log("local pet attributes calculated",Number(req&&req.petIndex||0));
      }
      else if(Resp===rp.PetGrowupExpRsp){
        r=makeOfflinePetGrowupRsp(req,r);
      }
      else if(Resp===rp.GetPetStorageRsp){
        r=makeOfflinePetStorageRsp(r);
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
      else if(Resp===rp.QuickHangupOperateRsp){
        var usedBefore=quickCombatUsed,operate=Number(req&&req.operate||0);
        if(operate>0&&quickCombatUsed<1){quickCombatUsed++;addLocalGold(10000);}
        r.ret=0;r.todayUseCount=quickCombatUsed;r.maxDayUseCount=1;
        r.todayBuyCount=0;r.maxDayBuyCount=0;
        r.awards=[offlineAction(rp.Action.ActionTye.ADD_GOLD,[10000])];
        if(usedBefore!==quickCombatUsed)save();
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
    bots:bots().map(function(x){return {name:x.name,level:x.level,offline:true};})
  };
  setInterval(save,15000);window.addEventListener("beforeunload",save);log("offline patch installed");
})();
"""

OVERLAY = """
<style id="offline-menu-style">
#offline-menu-button{position:fixed;z-index:2147483646;right:100px;top:5px;padding:4px 6px;border-radius:8px;background:rgba(17,25,46,.9);border:1px solid #64c8ff;color:#fff;font:11px sans-serif}
#offline-menu-panel{position:fixed;z-index:2147483647;right:10px;top:42px;width:220px;padding:12px;border-radius:12px;background:rgba(12,18,36,.97);border:1px solid #64c8ff;color:#fff;font:14px sans-serif;display:none}
#offline-menu-panel h3{margin:0 0 8px;font-size:16px;color:#8de2ff}
#offline-menu-panel .stat{font-size:12px;line-height:1.6;margin-bottom:8px;color:#d6edff}
#offline-menu-panel button{width:100%;margin:4px 0;padding:8px;border:0;border-radius:8px;background:#287bb6;color:#fff;font-size:13px}
#offline-menu-panel .danger{background:#9e3946}.offline-note{font-size:11px;color:#ffdd9c;margin-top:7px;line-height:1.4}
</style>
<div id="offline-menu-button">离线菜单</div>
<div id="offline-menu-panel"><h3>超级精灵球 · 离线工具</h3><div id="offline-stat" class="stat">本地存档加载中…</div>
<button data-act="gold">金币 +100万</button><button data-act="diamond">钻石 +1万</button><button data-act="cash">点券 +1万</button><button data-act="save">立即保存</button><button data-act="reset" class="danger">重置本地存档</button>
<div class="offline-note">模拟训练师为本地虚构数据，不连接在线排行榜；离线解锁不涉及真实支付。</div></div>
<script>
(function(){var n=0,t=setInterval(function(){n++;if(!window.OfflineGame&&n<120)return;clearInterval(t);var b=document.getElementById("offline-menu-button"),p=document.getElementById("offline-menu-panel"),s=document.getElementById("offline-stat");if(!b||!p)return;
b.onclick=function(){p.style.display=p.style.display==="block"?"none":"block";if(window.OfflineGame)s.textContent=JSON.stringify(OfflineGame.getState());};
p.onclick=function(e){var a=e.target&&e.target.getAttribute("data-act");if(!a||!window.OfflineGame)return;try{if(a==="gold")OfflineGame.addGold(1000000);if(a==="diamond")OfflineGame.addDiamond(10000);if(a==="cash")OfflineGame.addCash(10000);if(a==="save")OfflineGame.saveAndNotify();if(a==="reset"&&confirm("确定清除本设备的离线存档吗？"))OfflineGame.reset();s.textContent=JSON.stringify(OfflineGame.getState());}catch(x){console.error(x);}};
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
