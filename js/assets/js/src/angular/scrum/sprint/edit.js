var App = angular.module('intranet');


App.controller('sprintEditCtrl', function($scope, $http, $dialog) {
  if(board){
    $scope.columns = board;
  } else {
    $scope.columns = [{name: 'example name', sections: [{name: 'example name', cond: ''}]}];
  }

  $scope.columns_json = function(){
    return angular.toJson($scope.columns);
  };

  $scope.boards = [];
  $scope.selected_board = undefined;
  $http.get('/api/boards').success(function(data){
    $scope.boards = data.boards;
    $scope.boards.reverse();
    if($scope.boards.length > 0){
      $scope.selected_board = $scope.boards[0];
    }
  });

  $scope.choose = function(){
    $scope.columns = angular.fromJson($scope.selected_board.board);
  };

  $scope.delete = function(){
    var r = confirm("Press a button!");
    if(r === true){
      $http.delete('/api/boards/' + $scope.selected_board.id).success(function(){
        var index = $scope.boards.indexOf($scope.selected_board);
        $scope.boards.splice(index, 1);
        $scope.selected_board = $scope.boards[0];
      });
    }
  };

  $scope.save = function(){
    var name = prompt('Name');
    var data = {
      'name': name,
      'board': angular.toJson($scope.columns)
    };

    $http.post('/api/boards', data).success(function(response){
      data.id = response.id;
      $scope.boards.push(data);
      $scope.selected_board = $scope.boards[0];
    });
  };

  $scope.add_column = function(){
    $scope.columns.push({name: 'example name', sections: [{name: 'example name', cond: ''}]})
  };

  $scope.add_section = function(column){
    column.sections.push({name: 'example', cond: ''})
  };

  $scope.remove_column = function(column){
    var index = $scope.columns.indexOf(column);
    $scope.columns.splice(index, 1);
  };

  $scope.remove_section = function(section, sections){
    var index = sections.indexOf(section);
    sections.splice(index, 1);
  };

  $scope.show_bugs = function(){
    var d = $dialog.dialog({
      resolve: {
      }
    });
    d.open('scrum/sprint/bugsJson.html', 'sprintBugsJsonCtrl');

  };
});

App.controller('sprintBugsJsonCtrl', function($scope, $http, dialog, $dialog){
  $scope.close = function() {
    dialog.close();
  };
  var promise = $http.get('/api/sprint/' + sprint_id + '/bugs')
  promise.success(function(response){
    $scope.bugs = JSON.stringify(angular.fromJson(response), undefined, 4);
  });

  $scope.bugs_error = false;
  promise.error(function(response){
    $scope.bugs_error = true
  });
});
